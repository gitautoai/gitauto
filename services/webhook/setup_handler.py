import os
from anthropic.types import MessageParam, TextBlockParam

from constants.agent import MAX_ITERATIONS
from constants.ci import (
    CI_CONFIG_FILES,
    GHA_WORKFLOW_DIR,
    GITAUTO_COVERAGE_WORKFLOW_TEMPLATES_DIR,
)
from constants.claude import ClaudeModelId
from constants.system_messages.setup_handler import (
    SETUP_HANDLER_SYSTEM_MESSAGE,
    SETUP_PR_BODY,
)
from services.chat_with_agent import chat_with_agent
from services.git.create_empty_commit import create_empty_commit
from services.git.create_remote_branch import create_remote_branch
from services.git.delete_remote_branch import delete_remote_branch
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.get_default_branch import get_default_branch
from services.git.get_latest_remote_commit_sha import get_latest_remote_commit_sha
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.claude.tools.tools import TOOLS_FOR_SETUP
from services.github.pulls.close_pull_request import close_pull_request
from services.github.pulls.create_pull_request import create_pull_request
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.repositories.is_repo_forked import is_repo_forked
from services.github.users.get_email_from_commits import get_email_from_commits
from services.github.users.get_user_public_email import get_user_public_info
from services.slack.slack_notify import slack_notify
from services.supabase.usage.insert_usage import insert_usage
from services.supabase.usage.update_usage import update_usage
from services.supabase.installations.get_installation_by_owner import (
    get_installation_by_owner,
)
from services.supabase.repositories.get_repository_by_name import get_repository_by_name
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.generate_branch_name import generate_branch_name
from utils.logging.logging_config import (
    logger,
    set_owner_repo,
    set_pr_number,
    set_trigger,
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def setup_handler(
    owner_name: str,
    repo_name: str,
    token: str,
    sender_id: int,
    sender_name: str,
    source: str,
):
    set_owner_repo(owner_name, repo_name)
    set_trigger("setup")
    logger.info(
        "Setup triggered by sender_name=%s sender_id=%d source=%s for %s/%s",
        sender_name,
        sender_id,
        source,
        owner_name,
        repo_name,
    )
    thread_ts = slack_notify(
        f"Setup started for {owner_name}/{repo_name} by {sender_name} from {source}"
    )

    installation = get_installation_by_owner(owner_name)
    if not installation:
        logger.warning("No installation found for %s", owner_name)
        slack_notify(
            f"Setup skipped for {owner_name}/{repo_name}: no installation found",
            thread_ts=thread_ts,
        )
        return
    installation_id = installation["installation_id"]
    owner_id = installation["owner_id"]
    owner_type = installation["owner_type"]

    repository = get_repository_by_name(owner_id, repo_name)
    repo_id = repository["repo_id"] if repository else 0
    if repository and repository.get("target_branch"):
        target_branch = repository["target_branch"]
        logger.info("Using target_branch: %s", target_branch)
    else:
        clone_url = get_clone_url(owner_name, repo_name, token)
        target_branch = get_default_branch(clone_url=clone_url)
        if not target_branch:
            logger.info("Repository %s/%s is empty, skipping", owner_name, repo_name)
            slack_notify(
                f"Setup skipped for {owner_name}/{repo_name}: repository is empty",
                thread_ts=thread_ts,
            )
            return
        logger.info("Using default branch as target: %s", target_branch)

    clone_url = get_clone_url(owner_name, repo_name, token)

    # Clone to /tmp for reading files
    clone_dir = get_clone_dir(owner_name, repo_name, pr_number=None)
    git_clone_to_tmp(clone_dir, clone_url, target_branch)
    root_files = [
        f for f in os.listdir(clone_dir) if os.path.isfile(os.path.join(clone_dir, f))
    ]

    # Look up sender info from GitHub
    sender_info = get_user_public_info(username=sender_name, token=token)
    sender_email = sender_info.email
    if not sender_email:
        sender_email = get_email_from_commits(
            owner=owner_name, repo=repo_name, username=sender_name, token=token
        )

    # Create a branch for the coverage workflow PR
    new_branch = generate_branch_name(trigger="setup")
    # Must match: website/app/actions/github/get-open-setup-pr.ts
    title = "Set up test coverage workflow"
    base_args: BaseArgs = {
        "owner": owner_name,
        "owner_id": owner_id,
        "owner_type": owner_type,
        "repo": repo_name,
        "repo_id": repo_id,
        "clone_url": clone_url,
        "token": token,
        "installation_id": installation_id,
        "base_branch": target_branch,
        "new_branch": new_branch,
        "clone_dir": clone_dir,
        "is_fork": is_repo_forked(owner=owner_name, repo=repo_name, token=token),
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "sender_display_name": sender_info.display_name,
        "reviewers": [sender_name] if sender_name else [],
        "github_urls": [],
        "other_urls": [],
        "pr_number": 0,  # Set after create_pull_request below
        "pr_title": title,
        "pr_body": SETUP_PR_BODY,
        "pr_comments": [],
        "pr_creator": sender_name,
    }

    sha = get_latest_remote_commit_sha(clone_url=clone_url, base_args=base_args)
    create_remote_branch(sha=sha, base_args=base_args)
    create_empty_commit(
        base_args=base_args, message="Initial empty commit to create PR [skip ci]"
    )
    pr_url, pr_number = create_pull_request(
        body=SETUP_PR_BODY,
        title=title,
        base_args=base_args,
    )
    base_args["pr_number"] = pr_number
    set_pr_number(pr_number)
    logger.info("Created coverage PR %s/%s#%d", owner_name, repo_name, pr_number)

    usage_id = insert_usage(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        pr_number=pr_number,
        user_id=sender_id,
        user_name=sender_name,
        installation_id=installation_id,
        source="setup_handler",
        trigger="setup",
    )

    # Read all existing CI configs from local clone
    ci_configs: dict[str, str] = {}

    # GitHub Actions workflows (multiple .yml files in a directory)
    local_workflow_dir = os.path.join(clone_dir, GHA_WORKFLOW_DIR)
    if os.path.isdir(local_workflow_dir):
        for filename in os.listdir(local_workflow_dir):
            if not filename.endswith(".yml"):
                logger.info("Skipping non-YAML file: %s", filename)
                continue
            content = read_local_file(file_path=filename, base_dir=local_workflow_dir)
            if content:
                ci_configs[f"{GHA_WORKFLOW_DIR}/{filename} (GitHub Actions)"] = (
                    format_content_with_line_numbers(
                        file_path=f"{GHA_WORKFLOW_DIR}/{filename}", content=content
                    )
                )

    # Other CI systems (single config files each)
    for config_path, ci_name in CI_CONFIG_FILES:
        full_path = os.path.join(clone_dir, config_path)
        if os.path.isfile(full_path):
            content = read_local_file(file_path=config_path, base_dir=clone_dir)
            if content:
                ci_configs[f"{config_path} ({ci_name})"] = (
                    format_content_with_line_numbers(
                        file_path=config_path, content=content
                    )
                )

    logger.info("Detected CI configs: %s", list(ci_configs.keys()))

    # One example template is enough - Claude knows how to write workflows for any language
    raw_template = (
        read_local_file(
            file_path="pytest.yml", base_dir=GITAUTO_COVERAGE_WORKFLOW_TEMPLATES_DIR
        )
        or ""
    )
    example_template = (
        format_content_with_line_numbers(file_path="pytest.yml", content=raw_template)
        if raw_template
        else ""
    )

    user_content: list[TextBlockParam] = [
        {"type": "text", "text": f"Root files: {root_files}"},
        {"type": "text", "text": f"Target branch: {target_branch}"},
        {"type": "text", "text": f"Existing CI configs:\n{ci_configs}"},
        {"type": "text", "text": f"Example template (pytest.yml):\n{example_template}"},
    ]

    messages: list[MessageParam] = [{"role": "user", "content": user_content}]

    logger.info(
        "Calling Claude for setup (root files: %d, CI configs: %d)",
        len(root_files),
        len(ci_configs),
    )

    total_token_input = 0
    total_token_output = 0
    is_completed = False

    completion_reason = ""
    for _iteration in range(MAX_ITERATIONS):
        result = await chat_with_agent(
            messages=messages,
            system_message=SETUP_HANDLER_SYSTEM_MESSAGE,
            base_args=base_args,
            tools=TOOLS_FOR_SETUP,
            usage_id=usage_id,
            allow_edit_any_file=True,
            restrict_edit_to_target_test_file_only=False,
            allowed_to_edit_files=set(),
            model_id=ClaudeModelId.OPUS_4_6,  # Needs accurate analysis of existing workflows
        )
        messages = result.messages
        total_token_input += result.token_input
        total_token_output += result.token_output
        completion_reason = result.completion_reason

        if result.is_completed:
            logger.info("Setup agent completed successfully")
            is_completed = True
            break

    logger.info(
        "Setup agent used %d input tokens, %d output tokens",
        total_token_input,
        total_token_output,
    )

    if usage_id:
        update_usage(
            usage_id=usage_id,
            is_completed=is_completed,
            pr_number=pr_number,
            token_input=total_token_input,
            token_output=total_token_output,
        )

    # Check if the PR has actual file changes
    pr_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )

    if is_completed and pr_files:
        logger.info("Setup PR has %d file changes", len(pr_files))
        slack_notify(
            f"Setup completed for {owner_name}/{repo_name}#{pr_number}\n{pr_url}",
            thread_ts=thread_ts,
        )
    else:
        logger.info("Closing PR, no file changes. Agent: %s", completion_reason)
        close_pull_request(pr_number=pr_number, base_args=base_args)
        delete_remote_branch(base_args=base_args)
        slack_notify(
            f"Setup closed for {owner_name}/{repo_name}: {completion_reason}",
            thread_ts=thread_ts,
        )
