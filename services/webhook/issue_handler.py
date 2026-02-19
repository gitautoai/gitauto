# Standard imports
import asyncio
from datetime import datetime
from json import dumps
from pathlib import Path
import time

# Third-party imports
from anthropic.types import MessageParam

# Local imports
from config import PRODUCT_ID, PR_BODY_STARTS_WITH
from constants.agent import MAX_ITERATIONS
from constants.messages import COMPLETED_PR, SETTINGS_LINKS
from services.agents.verify_task_is_ready import verify_task_is_ready
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.chat_with_agent import chat_with_agent
from services.efs.get_efs_dir import get_efs_dir
from services.node.ensure_node_packages import ensure_node_packages
from services.node.set_npm_token_env import set_npm_token_env
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import clone_tasks, git_clone_to_efs
from services.git.prepare_repo_for_work import prepare_repo_for_work
from services.github.branches.create_remote_branch import create_remote_branch
from services.github.comments.create_comment import create_comment
from services.github.comments.delete_comments_by_identifiers import (
    delete_comments_by_identifiers,
)
from services.github.comments.get_comments import get_comments
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.commits.get_latest_remote_commit_sha import (
    get_latest_remote_commit_sha,
)
from services.github.commits.replace_remote_file import replace_remote_file_content
from services.github.files.get_raw_content import get_raw_content
from services.github.files.get_remote_file_content_by_url import (
    get_remote_file_content_by_url,
)
from services.github.markdown.render_text import render_text
from services.github.pulls.create_pull_request import create_pull_request
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.reactions.add_reaction_to_issue import add_reaction_to_issue
from services.github.trees.get_local_file_tree import get_local_file_tree
from services.github.types.github_types import GitHubLabeledPayload
from services.github.utils.deconstruct_github_payload import deconstruct_github_payload
from services.claude.tools.tools import TOOLS_FOR_ISSUES
from services.openai.vision import describe_image
from services.resend.send_email import send_email
from services.resend.text.credits_depleted_email import get_credits_depleted_email_text
from services.slack.slack_notify import slack_notify
from services.supabase.create_user_request import create_user_request
from services.supabase.credits.insert_credit import insert_credit
from services.supabase.owners.get_owner import get_owner
from services.supabase.owners.get_stripe_customer_id import get_stripe_customer_id
from services.supabase.owners.update_stripe_customer_id import update_stripe_customer_id
from services.supabase.repository_features.get_repository_features import (
    get_repository_features,
)
from services.supabase.usage.insert_usage import Trigger
from services.supabase.usage.update_usage import update_usage
from services.supabase.users.get_user import get_user
from services.stripe.check_availability import check_availability
from services.stripe.create_stripe_customer import create_stripe_customer
from services.webhook.utils.create_system_message import create_system_message
from services.claude.evaluate_condition import EvaluationResult
from services.claude.is_code_untestable import is_code_untestable
from services.supabase.coverages.get_coverages import get_coverages
from services.webhook.utils.should_bail import should_bail
from utils.files.get_impl_file_from_issue_title import get_impl_file_from_issue_title
from utils.files.find_test_files import find_test_files
from utils.files.is_config_file import is_config_file
from utils.files.read_local_file import read_local_file
from utils.files.is_test_file import is_test_file
from utils.files.merge_test_file_headers import merge_test_file_headers
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.images.get_base64 import get_base64
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger, set_pr_number, set_trigger
from utils.progress_bar.progress_bar import create_progress_bar
from utils.text.comment_identifiers import PROGRESS_BAR_EMPTY, PROGRESS_BAR_FILLED
from utils.text.text_copy import (
    UPDATE_COMMENT_FOR_422,
    git_command,
    pull_request_completed,
)
from utils.urls.extract_urls import extract_image_urls


async def create_pr_from_issue(
    payload: GitHubLabeledPayload,
    trigger: Trigger,
    lambda_info: dict[str, str | None] | None = None,
) -> None:
    set_trigger(trigger)
    current_time: float = time.time()

    # Extract label and validate it
    if (
        trigger == "issue_label"
        and "label" in payload
        and payload["label"]["name"] != PRODUCT_ID
    ):
        return

    # Deconstruct payload
    base_args, repo_settings = deconstruct_github_payload(payload=payload)

    # Ensure skip_ci is set to True for development commits
    base_args["skip_ci"] = True

    # Get some base args for early notifications
    owner_name = base_args["owner"]
    repo_name = base_args["repo"]
    issue_number = base_args["issue_number"]
    issue_title = base_args["issue_title"]
    sender_name = base_args["sender_name"]
    token = base_args["token"]

    # Start notification
    start_msg = f"Issue handler started: `{trigger}` by `{sender_name}` for `{issue_number}:{issue_title}` in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)

    # Delete all comments made by GitAuto except the one with the checkbox to clean up the issue
    gitauto_identifiers = [
        COMPLETED_PR,
        UPDATE_COMMENT_FOR_422,
        PROGRESS_BAR_FILLED,
        PROGRESS_BAR_EMPTY,
    ]
    delete_comments_by_identifiers(
        owner=owner_name,
        repo=repo_name,
        issue_number=issue_number,
        token=token,
        identifiers=gitauto_identifiers,
    )

    # Create a comment to track progress
    p = 0
    log_messages = []
    msg = "Got your request."
    add_log_message(msg, log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    comment_url = create_comment(body=comment_body, base_args=base_args)
    base_args["comment_url"] = comment_url

    # Get owner and repo metadata
    installation_id = base_args["installation_id"]
    owner_id = base_args["owner_id"]
    owner_type = base_args["owner_type"]
    repo_id = base_args["repo_id"]
    set_npm_token_env(owner_id)

    # Extract issue metadata
    issue_body = base_args["issue_body"].replace(SETTINGS_LINKS, "").strip()
    issue_body_rendered = render_text(base_args=base_args, text=issue_body)
    issuer_name = base_args["issuer_name"]
    parent_issue_title = base_args.get("parent_issue_title")
    parent_issue_body = base_args.get("parent_issue_body")

    # Extract more base args
    new_branch_name = base_args["new_branch"]
    sender_id = base_args["sender_id"]
    sender_email = base_args["sender_email"]
    github_urls = base_args["github_urls"]
    # other_urls = base_args["other_urls"]
    is_automation = base_args["is_automation"]

    # Get repository features
    repo_features = get_repository_features(owner_id=owner_id, repo_id=repo_id)
    restrict_edit_to_target_test_file_only = (
        repo_features["restrict_edit_to_target_test_file_only"]
        if repo_features
        else True
    )
    allow_edit_any_file = (
        repo_features["allow_edit_any_file"] if repo_features else False
    )

    p += 5
    add_log_message("Extracted metadata.", log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Ensure stripe customer exists (create if needed)
    stripe_customer_id = get_stripe_customer_id(owner_id)
    if not stripe_customer_id:
        stripe_customer_id = create_stripe_customer(
            owner_id=owner_id,
            owner_name=owner_name,
            installation_id=installation_id,
            user_id=sender_id if sender_id else 0,
            user_name=sender_name if sender_name else "unknown",
        )
        if stripe_customer_id:
            update_stripe_customer_id(owner_id, stripe_customer_id)

    # Now check availability (stripe_customer_id will exist or be None if creation failed)
    availability_status = check_availability(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        installation_id=installation_id,
        sender_name=sender_name,
    )

    can_proceed = availability_status["can_proceed"]
    user_message = availability_status["user_message"]
    billing_type = availability_status["billing_type"]

    if availability_status["log_message"] and can_proceed:
        add_log_message(availability_status["log_message"], log_messages)

    p += 5
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Notify the user if access is denied and early return
    if not can_proceed:
        body = user_message
        update_comment(body=body, base_args=base_args)
        logger.info(body)

        # Send email notification if user is a credit user and has zero credits
        # Disabled: This would send emails every time schedule trigger runs, annoying users
        # if is_credit_user and sender_id:
        #     user = get_user(user_id=sender_id)
        #     if user and user.get("email"):
        #         subject, text = get_no_credits_email_text(sender_name)
        #         send_email(to=user["email"], subject=subject, text=text)

        # Early return notification
        slack_notify(availability_status["log_message"], thread_ts)
        return

    # Start clone and install tasks early to run in parallel with LLM processing
    base_branch = base_args["base_branch"]
    efs_dir = get_efs_dir(owner_name, repo_name)
    clone_url = get_clone_url(owner_name, repo_name, token)
    clone_tasks[efs_dir] = asyncio.create_task(
        git_clone_to_efs(efs_dir, clone_url, base_branch)
    )
    node_ready = await ensure_node_packages(
        owner_name, owner_id, repo_name, base_branch, token, efs_dir
    )
    logger.info("node: ready=%s", node_ready)

    # Create a usage record
    usage_id = create_user_request(
        user_id=sender_id,
        user_name=sender_name,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        issue_number=issue_number,
        source="github",
        trigger=trigger,
        email=sender_email,
        lambda_info=lambda_info,
    )

    # Insert credit usage immediately (charge regardless of completion)
    if billing_type == "credit":
        insert_credit(owner_id=owner_id, transaction_type="usage", usage_id=usage_id)

    add_reaction_to_issue(
        issue_number=issue_number, content="eyes", base_args=base_args
    )

    # Check out the issue comments
    issue_comments = get_comments(issue_number=issue_number, base_args=base_args)
    comment_body = f"Found {len(issue_comments)} issue comments."
    p += 5
    add_log_message(comment_body, log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Check out the image URLs in the issue body and comments
    image_urls = extract_image_urls(text=issue_body_rendered)
    if image_urls:
        comment_body = f"Found {len(image_urls)} images in the issue body."
        p += 5
        add_log_message(comment_body, log_messages)
        update_comment(
            body=create_progress_bar(p=p, msg="\n".join(log_messages)),
            base_args=base_args,
        )

    for issue_comment in issue_comments:
        issue_comment_rendered = render_text(base_args=base_args, text=issue_comment)
        image_urls.extend(extract_image_urls(text=issue_comment_rendered))
    for url in image_urls:
        # Check if URL has a valid image extension (OpenAI only supports: png, jpeg, gif, webp)
        image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
        if not any(url["url"].lower().endswith(ext) for ext in image_extensions):
            logger.warning(
                "Skipping non-image URL or unsupported format: %s", url["url"]
            )
            continue

        base64_image = get_base64(url=url["url"])

        if not base64_image:
            logger.warning("Failed to fetch image from URL: %s", url["url"])
            continue

        context = f"## Issue:\n{issue_title}\n\n## Issue Body:\n{issue_body}\n\n## Issue Comments:\n{'\n'.join(issue_comments)}"
        description = describe_image(base64_image=base64_image, context=context)
        description = f"## {url['alt']}\n\n{description}"
        issue_comments.append(description)
        create_comment(body=description, base_args=base_args)

    # Check out the URLs in the issue body
    reference_file_paths: set[str] = set()
    reference_contents: list[str] = []
    for url in github_urls:
        comment_body = "Also checking out the URLs in the issue body."
        p += 5
        add_log_message(comment_body, log_messages)
        update_comment(
            body=create_progress_bar(p=p, msg="\n".join(log_messages)),
            base_args=base_args,
        )
        file_path, content = get_remote_file_content_by_url(url=url, token=token)
        logger.info("```%s\n%s```\n", url, content)
        reference_file_paths.add(file_path)
        reference_contents.append(content)

    today = datetime.now().strftime("%Y-%m-%d")

    # Extract target implementation file
    impl_file_path = get_impl_file_from_issue_title(issue_title)
    test_dir_prefixes = repo_settings["test_dir_prefixes"] if repo_settings else []

    # Skip fetching impl_file if already in reference_contents (avoids duplicate)
    impl_file_content = ""
    if impl_file_path not in reference_file_paths:
        impl_file_content = get_raw_content(
            owner=owner_name,
            repo=repo_name,
            file_path=impl_file_path,
            ref=base_branch,
            token=token,
        )
    test_files: dict[str, str] = {}
    p += 5
    add_log_message(f"Read target file: `{impl_file_path}`", log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)),
        base_args=base_args,
    )

    # Check if uncovered code is untestable (for schedule-triggered coverage issues)
    untestable_code_info: EvaluationResult | None = None
    coverage_dict = get_coverages(owner_id, repo_id, [impl_file_path])
    coverage_data = coverage_dict.get(impl_file_path)
    if coverage_data and impl_file_content:
        uncovered_lines = coverage_data.get("uncovered_lines")
        uncovered_functions = coverage_data.get("uncovered_functions")
        uncovered_branches = coverage_data.get("uncovered_branches")
        if uncovered_lines or uncovered_functions or uncovered_branches:
            untestable_code_info = is_code_untestable(
                file_path=impl_file_path,
                file_content=impl_file_content,
                uncovered_lines=uncovered_lines,
                uncovered_functions=uncovered_functions,
                uncovered_branches=uncovered_branches,
            )
            logger.info(
                "Untestable code check for %s: %s", impl_file_path, untestable_code_info
            )
            if untestable_code_info.result:
                p += 5
                add_log_message(
                    f"Detected untestable code in `{impl_file_path}`", log_messages
                )
                update_comment(
                    body=create_progress_bar(p=p, msg="\n".join(log_messages)),
                    base_args=base_args,
                )

    parent = str(Path(impl_file_path).parent)
    target_dir = parent if parent != "." else None

    user_input_obj: dict[str, object] = {
        "today": today,
        "owner": owner_name,
        "repo": repo_name,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "impl_file_path": impl_file_path,
    }

    # Only include non-empty values to reduce token usage
    if issue_comments:
        user_input_obj["issue_comments"] = issue_comments
    if parent_issue_title:
        user_input_obj["parent_issue_title"] = parent_issue_title
    if parent_issue_body:
        user_input_obj["parent_issue_body"] = parent_issue_body
    if target_dir:
        user_input_obj["target_dir"] = target_dir
    if test_dir_prefixes:
        user_input_obj["test_dir_prefixes"] = test_dir_prefixes

    # Create a remote branch
    latest_commit_sha = get_latest_remote_commit_sha(
        clone_url=base_args["clone_url"], base_args=base_args
    )
    create_remote_branch(sha=latest_commit_sha, base_args=base_args)
    comment_body = f"Created a branch: `{new_branch_name}`"
    p += 5
    add_log_message(comment_body, log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Create initial empty commit and PR early in the process
    comment_body = "Creating initial PR..."
    p += 5
    add_log_message(comment_body, log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )
    create_empty_commit(
        base_args=base_args, message="Initial empty commit to create PR [skip ci]"
    )

    issue_link: str = f"{PR_BODY_STARTS_WITH}{issue_number}\n\n"
    pr_body = issue_link + git_command(new_branch_name=new_branch_name)
    pr_url, pr_number = create_pull_request(
        body=pr_body, title=issue_title, base_args=base_args
    )
    set_pr_number(pr_number)
    base_args["pull_number"] = pr_number

    # Clone repo to tmp (runs in parallel with remaining work, awaited before exit)
    clone_dir = get_clone_dir(owner_name, repo_name, pr_number)
    base_args["clone_dir"] = clone_dir
    await prepare_repo_for_work(
        owner=owner_name,
        repo=repo_name,
        pr_branch=new_branch_name,
        token=token,
        clone_dir=clone_dir,
    )

    # List file tree from local clone (now that clone_dir is available)
    root_files = get_local_file_tree(base_args=base_args, dir_path="")
    if root_files:
        user_input_obj["root_files"] = root_files
    if target_dir:
        target_dir_files = get_local_file_tree(base_args=base_args, dir_path=target_dir)
        if target_dir_files:
            user_input_obj["target_dir_files"] = target_dir_files

    # Search for test files in the local clone (/tmp, fast)
    test_file_paths = find_test_files(
        search_dir=clone_dir, impl_file_path=impl_file_path
    )
    max_test_files_in_prompt = 5
    include_contents = len(test_file_paths) <= max_test_files_in_prompt
    if include_contents:
        for test_path in test_file_paths:
            content = read_local_file(test_path, base_dir=clone_dir)
            if not content:
                continue

            test_files[test_path] = format_content_with_line_numbers(
                file_path=test_path, content=content
            )
            p += 5
            add_log_message(f"Found existing test file: `{test_path}`", log_messages)
            update_comment(
                body=create_progress_bar(p=p, msg="\n".join(log_messages)),
                base_args=base_args,
            )
    else:
        logger.info(
            "Too many test files (%d > %d) to include contents in prompt, passing paths only, let agent choose to read",
            len(test_file_paths),
            max_test_files_in_prompt,
        )
        for test_path in test_file_paths:
            add_log_message(f"Found existing test file: `{test_path}`", log_messages)

    logger.info("Test files found: %s", test_file_paths)

    # Build test_files into user_input
    if include_contents and test_files:
        user_input_obj["test_files"] = test_files
    elif test_file_paths:
        user_input_obj["test_file_paths"] = test_file_paths
    else:
        user_input_obj["test_files_not_found"] = (
            f"No test file found by searching the repo for '{Path(impl_file_path).stem}'. "
            "A test file may exist elsewhere in the repo. Search for it before creating a new one."
        )

    # Create messages for the agent
    user_input = dumps(user_input_obj)
    messages: list[MessageParam] = [{"role": "user", "content": user_input}]
    if impl_file_content:
        messages.append({"role": "user", "content": impl_file_content})
    for c in reference_contents:
        messages.append({"role": "user", "content": c})

    # Validate files for syntax issues before editing
    files_to_validate = list(
        {impl_file_path, *reference_file_paths, *test_files.keys()}
    )
    validation_result = await verify_task_is_ready(
        base_args=base_args,
        file_paths=files_to_validate,
        run_tsc=True,
        run_jest=False,
    )
    base_args["baseline_tsc_errors"] = set(validation_result.tsc_errors)
    pre_existing_errors = ""
    if validation_result.errors:
        pre_existing_errors = "\n".join(validation_result.errors)
        logger.warning("Remaining errors:\n%s", pre_existing_errors)
    fixes_applied = validation_result.fixes_applied

    comment_body = f"Created pull request: {pr_url}"
    p += 5
    add_log_message(comment_body, log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)),
        base_args=base_args,
    )

    # Notify agent of auto-fixes and remaining errors (in timeline order)
    allowed_to_edit_files = set(validation_result.files_with_errors)

    # If uncovered code is untestable, allow editing impl file and notify agent
    if untestable_code_info and untestable_code_info.result:
        untestable_reason = untestable_code_info.reason
        allowed_to_edit_files.add(impl_file_path)
        untestable_msg = f"Untestable code in `{impl_file_path}`: {untestable_reason}"
        messages.append({"role": "user", "content": untestable_msg})
        logger.info("Added untestable code message for %s", impl_file_path)

    if fixes_applied or pre_existing_errors:
        parts = ["## Prettier/ESLint Results\n"]
        parts.append("We ran Prettier and ESLint with --fix on the source files.\n")
        if fixes_applied:
            fixes_str = "\n".join(fixes_applied)
            parts.append(f"**Auto-fixed and committed:**\n{fixes_str}\n")
        if pre_existing_errors:
            parts.append(f"**Remaining unfixable errors:**\n{pre_existing_errors}\n")
        parts.append("Read the latest file content before making changes.")
        messages.append({"role": "user", "content": "\n".join(parts)})

    # Loop a process explore repo and commit changes until the ticket is resolved
    total_token_input = 0
    total_token_output = 0
    is_completed = False

    system_message = create_system_message(trigger=trigger, repo_settings=repo_settings)

    for _iteration in range(MAX_ITERATIONS):
        if should_bail(
            current_time=current_time,
            phase="issue processing",
            base_args=base_args,
            slack_thread_ts=None,
        ):
            break

        # Call the agent to explore the codebase and commit changes
        result = await chat_with_agent(
            messages=messages,
            system_message=system_message,
            base_args=base_args,
            tools=TOOLS_FOR_ISSUES,
            p=p,
            log_messages=log_messages,
            usage_id=usage_id,
            allow_edit_any_file=allow_edit_any_file,
            restrict_edit_to_target_test_file_only=restrict_edit_to_target_test_file_only,
            allowed_to_edit_files=allowed_to_edit_files,
            model_id=None,
        )
        messages = result.messages
        is_completed = result.is_completed
        p = result.p
        total_token_input += result.token_input
        total_token_output += result.token_output

        if is_completed:
            logger.info(
                "Agent signaled completion via verify_task_is_complete, breaking loop"
            )
            break

    # Log if loop exhausted without completion and force verification
    if not is_completed:
        logger.warning(
            "Agent loop hit MAX_ITERATIONS (%d) without calling verify_task_is_complete. Forcing verification.",
            MAX_ITERATIONS,
        )
        await verify_task_is_complete(base_args=base_args)

    # Add headers to test files before triggering CI
    last_commit_sha = ""
    changed_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pull_number=pr_number, token=token
    )

    for file_change in changed_files:
        file_path = file_change["filename"]
        if not is_test_file(file_path) or is_config_file(file_path):
            continue

        file_content = get_raw_content(
            owner=owner_name,
            repo=repo_name,
            file_path=file_path,
            ref=new_branch_name,
            token=token,
        )
        if not file_content:
            continue

        updated_content = merge_test_file_headers(file_content, file_path)
        if not updated_content or updated_content == file_content:
            continue

        result = replace_remote_file_content(
            file_content=updated_content,
            file_path=file_path,
            base_args=base_args,
        )
        if result.commit_sha:
            last_commit_sha = result.commit_sha

    # Trigger final test workflows with an empty commit
    comment_body = "Triggering workflows..."
    p += 5
    add_log_message(comment_body, log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )
    create_empty_commit(base_args=base_args, parent_sha=last_commit_sha)

    # Update the issue comment
    body_after_pr = pull_request_completed(
        issuer_name=issuer_name,
        sender_name=sender_name,
        pr_url=pr_url,
        is_automation=is_automation,
    )
    update_comment(body=body_after_pr, base_args=base_args)

    # Success notification
    success_msg = f"Work completed for {owner_name}/{repo_name} PR: {pr_url}"
    slack_notify(success_msg, thread_ts)

    end_time = time.time()
    if usage_id:
        update_usage(
            usage_id=usage_id,
            is_completed=is_completed,
            pr_number=pr_number,
            token_input=total_token_input,
            token_output=total_token_output,
            total_seconds=int(end_time - current_time),
        )

    # Check if user just ran out of credits and send casual notification
    if billing_type == "credit":
        owner = get_owner(owner_id=owner_id)
        if owner and owner["credit_balance_usd"] <= 0 and sender_id:
            user = get_user(user_id=sender_id)
            email = user.get("email") if user else None
            if email:
                subject, text = get_credits_depleted_email_text(sender_name)
                send_email(to=email, subject=subject, text=text)

    # End notification
    end_msg = "Completed" if is_completed else "@channel Failed"
    slack_notify(end_msg, thread_ts)
    return
