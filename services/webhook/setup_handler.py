import os
from typing import cast

from anthropic.types import MessageParam

from constants.agent import MAX_ITERATIONS
from constants.claude import ClaudeModelId
from constants.system_messages.setup_handler import (
    SETUP_HANDLER_SYSTEM_MESSAGE,
    SETUP_PR_BODY,
)
from services.chat_with_agent import chat_with_agent
from services.efs.get_efs_dir import get_efs_dir
from services.git.git_clone_to_efs import git_clone_to_efs
from services.git.get_clone_url import get_clone_url
from services.github.branches.create_remote_branch import create_remote_branch
from services.github.branches.delete_remote_branch import delete_remote_branch
from services.github.branches.get_default_branch import get_default_branch
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.commits.get_latest_remote_commit_sha import (
    get_latest_remote_commit_sha,
)
from services.claude.tools.tools import TOOLS_FOR_SETUP
from services.github.pulls.close_pull_request import close_pull_request
from services.github.pulls.create_pull_request import create_pull_request
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.types.github_types import BaseArgs
from services.slack.slack_notify import slack_notify
from services.supabase.usage.insert_usage import insert_usage
from services.supabase.usage.update_usage import update_usage
from services.supabase.installations.get_installation_by_owner import (
    get_installation_by_owner,
)
from services.supabase.repositories.get_repository_by_name import get_repository_by_name
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

WORKFLOW_DIR = ".github/workflows"
TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, "github", "workflows", "templates"
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def setup_handler(
    owner_name: str,
    repo_name: str,
    token: str,
    sender_name: str,
):
    set_owner_repo(owner_name, repo_name)
    set_trigger("setup")
    thread_ts = slack_notify(f"Setup started for {owner_name}/{repo_name}")

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
        target_branch, is_empty = get_default_branch(
            owner=owner_name, repo=repo_name, token=token
        )
        if is_empty:
            logger.info("Repository %s/%s is empty, skipping", owner_name, repo_name)
            slack_notify(
                f"Setup skipped for {owner_name}/{repo_name}: repository is empty",
                thread_ts=thread_ts,
            )
            return
        logger.info("Using default branch as target: %s", target_branch)

    efs_dir = get_efs_dir(owner_name, repo_name)
    clone_url = get_clone_url(owner_name, repo_name, token)
    await git_clone_to_efs(efs_dir=efs_dir, clone_url=clone_url, branch=target_branch)
    root_files = [
        f for f in os.listdir(efs_dir) if os.path.isfile(os.path.join(efs_dir, f))
    ]

    # Create a branch for the coverage workflow PR
    new_branch = generate_branch_name()
    base_args = cast(
        BaseArgs,
        {
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
            "clone_dir": efs_dir,
            "reviewers": [sender_name] if sender_name else [],
        },
    )

    sha = get_latest_remote_commit_sha(clone_url=clone_url, base_args=base_args)
    create_remote_branch(sha=sha, base_args=base_args)
    create_empty_commit(
        base_args=base_args, message="Initial empty commit to create PR [skip ci]"
    )
    pr_url, pr_number = create_pull_request(
        body=SETUP_PR_BODY,
        title="Set up test coverage workflow",
        base_args=base_args,
    )
    base_args["pull_number"] = pr_number
    set_pr_number(pr_number)
    logger.info("Created coverage PR %s/%s#%d", owner_name, repo_name, pr_number)

    usage_id = insert_usage(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        issue_number=0,
        user_id=0,
        installation_id=installation_id,
        source="setup_handler",
        trigger="setup",
        pr_number=pr_number,
    )

    # Read existing workflow files from local clone at EFS
    workflow_files: dict[str, str] = {}
    local_workflow_dir = os.path.join(efs_dir, WORKFLOW_DIR)
    if os.path.isdir(local_workflow_dir):
        for filename in os.listdir(local_workflow_dir):
            if not filename.endswith(".yml"):
                continue
            content = read_local_file(file_path=filename, base_dir=local_workflow_dir)
            if content:
                workflow_files[f"{WORKFLOW_DIR}/{filename}"] = (
                    format_content_with_line_numbers(
                        file_path=f"{WORKFLOW_DIR}/{filename}", content=content
                    )
                )

    # One example template is enough - Claude knows how to write workflows for any language
    raw_template = read_local_file(file_path="pytest.yml", base_dir=TEMPLATES_DIR) or ""
    example_template = (
        format_content_with_line_numbers(file_path="pytest.yml", content=raw_template)
        if raw_template
        else ""
    )

    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Root files: {root_files}"},
                {"type": "text", "text": f"Target branch: {target_branch}"},
                {"type": "text", "text": f"Existing workflows:\n{workflow_files}"},
                {
                    "type": "text",
                    "text": f"Example template (pytest.yml):\n{example_template}",
                },
            ],
        }
    ]

    logger.info(
        "Calling Claude for setup (root files: %d, existing workflows: %d)",
        len(root_files),
        len(workflow_files),
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
            model_id=ClaudeModelId.SONNET_4_6,  # Workflow YAML generation is straightforward
        )
        messages = result.messages
        total_token_input += result.token_input
        total_token_output += result.token_output
        completion_reason = result.completion_reason

        if result.is_completed:
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
        owner=owner_name, repo=repo_name, pull_number=pr_number, token=token
    )

    if is_completed and pr_files:
        slack_notify(
            f"Setup completed for {owner_name}/{repo_name}#{pr_number}\n{pr_url}",
            thread_ts=thread_ts,
        )
    else:
        logger.info("Closing PR, no file changes. Agent: %s", completion_reason)
        close_pull_request(pull_number=pr_number, base_args=base_args)
        delete_remote_branch(base_args=base_args)
        slack_notify(
            f"Setup closed for {owner_name}/{repo_name}: {completion_reason}",
            thread_ts=thread_ts,
        )
