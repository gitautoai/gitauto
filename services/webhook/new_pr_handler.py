# Standard imports
from datetime import datetime
from json import dumps
from pathlib import Path
import time

# Third-party imports
from anthropic.types import MessageParam

# Local imports
from constants.agent import MAX_ITERATIONS
from constants.messages import SETTINGS_LINKS
from constants.triggers import NewPrTrigger
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.agents.verify_task_is_ready import verify_task_is_ready
from services.chat_with_agent import chat_with_agent
from services.claude.is_code_untestable import CodeAnalysisResult, is_code_untestable
from services.claude.tools.tools import TOOLS_FOR_ISSUES
from services.git.create_empty_commit import create_empty_commit
from services.git.get_clone_dir import get_clone_dir
from services.git.clone_repo_and_install_dependencies import (
    clone_repo_and_install_dependencies,
)
from services.git.write_and_commit_file import write_and_commit_file
from services.github.comments.create_comment import create_comment
from services.github.comments.get_comments import get_comments
from services.github.comments.update_comment import update_comment
from services.github.files.get_remote_file_content_by_url import (
    get_remote_file_content_by_url,
)
from services.github.markdown.render_text import render_text
from services.github.pulls.close_pull_request import close_pull_request
from services.github.pulls.generate_and_upsert_pr_body_section import (
    generate_and_upsert_pr_body_section,
)
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.types.github_types import PrLabeledPayload
from services.github.utils.deconstruct_github_payload import deconstruct_github_payload
from services.node.ensure_node_packages import ensure_node_packages
from services.node.set_npm_token_env import set_npm_token_env
from services.openai.vision import describe_image
from services.php.ensure_php_packages import ensure_php_packages
from services.python.ensure_python_packages import ensure_python_packages
from services.resend.send_email import send_email
from services.resend.text.credits_depleted_email import get_credits_depleted_email_text
from services.slack.slack_notify import slack_notify
from services.stripe.check_availability import check_availability
from services.stripe.create_stripe_customer import create_stripe_customer
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.create_user_request import create_user_request
from services.supabase.credits.check_purchase_exists import check_purchase_exists
from services.supabase.credits.insert_credit import insert_credit
from services.supabase.email_sends.insert_email_send import insert_email_send
from services.supabase.email_sends.update_email_send import update_email_send
from services.supabase.owners.get_owner import get_owner
from services.supabase.owners.get_stripe_customer_id import get_stripe_customer_id
from services.supabase.owners.update_stripe_customer_id import update_stripe_customer_id
from services.supabase.usage.update_usage import update_usage
from services.supabase.users.get_user import get_user
from services.webhook.utils.create_system_message import create_system_message
from services.webhook.utils.get_preferred_model import get_preferred_model
from services.webhook.utils.should_bail import should_bail
from utils.command.run_subprocess import run_subprocess
from utils.files.detect_test_location_convention import detect_test_location_convention
from utils.files.detect_test_naming_convention import detect_test_naming_convention
from utils.files.find_test_files import find_test_files
from utils.files.get_impl_file_from_pr_title import get_impl_file_from_pr_title
from utils.files.get_local_file_tree import get_local_file_tree
from utils.files.is_config_file import is_config_file
from utils.files.is_test_file import is_test_file
from utils.files.merge_test_file_headers import merge_test_file_headers
from utils.files.prioritize_test_files import prioritize_test_files
from utils.files.read_local_file import read_local_file
from utils.files.should_skip_test import should_skip_test
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.images.get_base64 import get_base64
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger
from utils.memory.gc_collect_and_log import gc_collect_and_log
from utils.pr_templates.schedule import SCHEDULE_PREFIX_INCREASE
from utils.progress_bar.progress_bar import create_progress_bar
from utils.text.build_pr_completion_comment import build_pr_completion_comment
from utils.urls.extract_urls import extract_image_urls


async def handle_new_pr(
    payload: PrLabeledPayload,
    trigger: NewPrTrigger,
    lambda_info: dict[str, str | None] | None = None,
) -> None:
    current_time: float = time.time()

    # Deconstruct payload
    base_args, repo_settings = deconstruct_github_payload(payload=payload)

    pr_number = payload["number"]
    base_args["pr_number"] = pr_number
    pr_url = payload["pull_request"]["html_url"]

    base_args["trigger"] = trigger
    # Ensure skip_ci is set to True for development commits
    base_args["skip_ci"] = True

    # Get some base args for early notifications
    owner_name = base_args["owner"]
    repo_name = base_args["repo"]
    token = base_args["token"]
    pr_title = base_args["pr_title"]
    sender_name = base_args["sender_name"]

    # Start notification
    start_msg = f"PR handler started: `{trigger}` by `{sender_name}` for {pr_number}:{pr_title} in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)
    base_args["slack_thread_ts"] = thread_ts

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

    # Extract PR metadata
    pr_body = base_args["pr_body"].replace(SETTINGS_LINKS, "").strip()
    pr_body_rendered = render_text(base_args=base_args, text=pr_body)
    pr_creator = base_args["pr_creator"]

    # Extract more base args
    new_branch_name = base_args["new_branch"]
    sender_id = base_args["sender_id"]
    sender_email = base_args["sender_email"]
    sender_display_name = base_args["sender_display_name"]
    github_urls = base_args["github_urls"]

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
            updated_by = f"{sender_id}:{sender_name}" if sender_id else "system"
            update_stripe_customer_id(owner_id, stripe_customer_id, updated_by)

    # Now check availability (stripe_customer_id will exist or be None if creation failed)
    availability_status = check_availability(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        sender_name=sender_name,
    )

    can_proceed = availability_status["can_proceed"]
    user_message = availability_status["user_message"]
    billing_type = availability_status["billing_type"]

    # Resolve which model to use based on repo settings and whether owner has purchased credits
    has_purchased = check_purchase_exists(owner_id=owner_id)
    model_id = get_preferred_model(
        repo_settings=repo_settings,
        is_paid=has_purchased,
    )
    base_args["model_id"] = model_id

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
        pr_number=pr_number,
        source="github",
        trigger=trigger,
        email=sender_email,
        display_name=sender_display_name,
        lambda_info=lambda_info,
    )
    base_args["usage_id"] = usage_id

    # Insert credit usage immediately (charge regardless of completion)
    if billing_type == "credit":
        insert_credit(
            owner_id=owner_id,
            transaction_type="usage",
            usage_id=usage_id,
            model_id=model_id,
        )

    # Check out the PR comments
    pr_comments = get_comments(pr_number=pr_number, base_args=base_args)
    comment_body = f"Found {len(pr_comments)} PR comments."
    p += 5
    add_log_message(comment_body, log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Check out the image URLs in the PR body and comments
    image_urls = extract_image_urls(text=pr_body_rendered)
    if image_urls:
        comment_body = f"Found {len(image_urls)} images in the PR body."
        p += 5
        add_log_message(comment_body, log_messages)
        update_comment(
            body=create_progress_bar(p=p, msg="\n".join(log_messages)),
            base_args=base_args,
        )

    for pr_comment in pr_comments:
        pr_comment_rendered = render_text(base_args=base_args, text=pr_comment)
        image_urls.extend(extract_image_urls(text=pr_comment_rendered))
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

        context = f"## PR Title:\n{pr_title}\n\n## PR Body:\n{pr_body}\n\n## PR Comments:\n{'\n'.join(pr_comments)}"
        description = describe_image(base64_image=base64_image, context=context)
        description = f"## {url['alt']}\n\n{description}"
        pr_comments.append(description)
        create_comment(body=description, base_args=base_args)

    # Check out the URLs in the PR body
    reference_files: dict[str, str] = {}
    for url in github_urls:
        comment_body = "Also checking out the URLs in the PR body."
        p += 5
        add_log_message(comment_body, log_messages)
        update_comment(
            body=create_progress_bar(p=p, msg="\n".join(log_messages)),
            base_args=base_args,
        )
        file_path, content = get_remote_file_content_by_url(url=url, token=token)
        logger.info("```%s\n%s```\n", url, content)
        if file_path and content:
            reference_files[file_path] = format_content_with_line_numbers(
                file_path=file_path, content=content
            )

    today = datetime.now().strftime("%Y-%m-%d")

    # Extract target implementation file
    impl_file_path = get_impl_file_from_pr_title(pr_title)
    if not impl_file_path:
        raise ValueError(f"No file path found in PR title: {pr_title}")

    if pr_title.startswith(SCHEDULE_PREFIX_INCREASE):
        base_args["impl_file_to_collect_coverage_from"] = impl_file_path
    test_dir_prefixes = repo_settings["test_dir_prefixes"] if repo_settings else []

    test_files: dict[str, str] = {}
    parent = str(Path(impl_file_path).parent)
    target_dir = parent if parent != "." else None

    # Clone repo to tmp (runs in parallel with remaining work, awaited before exit)
    clone_dir = get_clone_dir(owner_name, repo_name, pr_number)
    base_args["clone_dir"] = clone_dir
    clone_repo_and_install_dependencies(
        owner=owner_name,
        repo=repo_name,
        base_branch=base_args["base_branch"],
        pr_branch=new_branch_name,
        token=token,
        clone_dir=clone_dir,
    )

    # Install dependencies (read repo files from clone_dir, cache on S3)
    node_ready = ensure_node_packages(
        owner_id=owner_id,
        clone_dir=clone_dir,
        owner_name=owner_name,
        repo_name=repo_name,
    )
    logger.info("node: ready=%s", node_ready)

    php_ready = ensure_php_packages(
        owner_id=owner_id,
        clone_dir=clone_dir,
        owner_name=owner_name,
        repo_name=repo_name,
    )
    logger.info("php: ready=%s", php_ready)

    python_ready = ensure_python_packages(
        owner_id=owner_id,
        clone_dir=clone_dir,
        owner_name=owner_name,
        repo_name=repo_name,
    )
    logger.info("python: ready=%s", python_ready)

    # Read impl file from local clone and skip if no testable code
    impl_file_content = (
        read_local_file(file_path=impl_file_path, base_dir=clone_dir) or ""
    )
    p += 5
    add_log_message(f"Read target file: `{impl_file_path}`", log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)),
        base_args=base_args,
    )
    if should_skip_test(impl_file_path, impl_file_content):
        msg = f"Closing PR: `{impl_file_path}` has no testable code (only docstrings, imports, constants, or type definitions)."
        logger.info(msg)
        add_log_message(msg, log_messages)
        update_comment(
            body=create_progress_bar(p=100, msg="\n".join(log_messages)),
            base_args=base_args,
        )
        close_pull_request(pr_number=base_args["pr_number"], base_args=base_args)
        return

    # Check if uncovered code is dead or untestable (for schedule-triggered coverage issues)
    untestable_code_info: CodeAnalysisResult | None = None
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
                "Dead/untestable code check for %s: %s",
                impl_file_path,
                untestable_code_info,
            )
            if untestable_code_info and untestable_code_info.result:
                p += 5
                add_log_message(
                    f"Detected dead/untestable code in `{impl_file_path}`", log_messages
                )
                update_comment(
                    body=create_progress_bar(p=p, msg="\n".join(log_messages)),
                    base_args=base_args,
                )

    # List file tree from local clone (now that clone_dir is available)
    root_files = get_local_file_tree(base_args=base_args, dir_path="")

    # Search for test files related to the impl file
    ls_result = run_subprocess(args=["git", "ls-files"], cwd=clone_dir)
    all_file_paths = (
        ls_result.stdout.strip().split("\n") if ls_result and ls_result.stdout else []
    )
    test_file_paths = find_test_files(impl_file_path, all_file_paths, test_dir_prefixes)
    test_file_paths = prioritize_test_files(test_file_paths, impl_file_path)
    base_args["test_file_paths"] = test_file_paths
    max_test_files_in_prompt = 5

    # Include most relevant test files with contents, rest as paths-only
    most_relevant_test_paths = test_file_paths[:max_test_files_in_prompt]
    remaining_test_paths = test_file_paths[max_test_files_in_prompt:]

    for test_path in most_relevant_test_paths:
        content = read_local_file(test_path, base_dir=clone_dir)
        if not content:
            continue
        test_files[test_path] = format_content_with_line_numbers(
            file_path=test_path, content=content
        )
        p += 5
        add_log_message(
            f"Found test file matching '{Path(impl_file_path).stem}': `{test_path}`",
            log_messages,
        )
        update_comment(
            body=create_progress_bar(p=p, msg="\n".join(log_messages)),
            base_args=base_args,
        )

    if remaining_test_paths:
        logger.info(
            "Including %d test files with contents, %d as paths only",
            len(most_relevant_test_paths),
            len(remaining_test_paths),
        )
        for test_path in remaining_test_paths:
            add_log_message(
                f"Found test file matching '{Path(impl_file_path).stem}': `{test_path}`",
                log_messages,
            )

    logger.info("Test files found: %s", test_file_paths)

    # Build user input for the agent
    user_input_obj: dict[str, object] = {
        "today": today,
        "owner": owner_name,
        "repo": repo_name,
        "pr_title": pr_title,
        "pr_body": pr_body,
        "impl_file_path": impl_file_path,
    }
    # Only include non-empty values to reduce token usage
    if pr_comments:
        user_input_obj["pr_comments"] = pr_comments
    if target_dir:
        user_input_obj["target_dir"] = target_dir
    if test_dir_prefixes:
        user_input_obj["test_dir_prefixes"] = test_dir_prefixes
    if root_files:
        user_input_obj["root_files"] = root_files
    if target_dir:
        target_dir_files = get_local_file_tree(base_args=base_args, dir_path=target_dir)
        if target_dir_files:
            user_input_obj["target_dir_files"] = target_dir_files
    if test_files:
        # list() needed: dict_keys is not JSON serializable; content is in separate messages
        user_input_obj["test_files_included"] = list(test_files.keys())
    if remaining_test_paths:
        user_input_obj["test_file_paths"] = remaining_test_paths
    if not test_files and not remaining_test_paths:
        search_term = Path(impl_file_path).stem
        user_input_obj["test_files_not_found"] = (
            f"No test file found by searching the repo for '{search_term}'. "
            "A test file may exist elsewhere in the repo. Search for it before creating a new one."
        )

    # Detect repo's test naming convention (e.g. .spec.ts, .test.ts, test_foo.py, FooTest.php)
    test_naming = detect_test_naming_convention(clone_dir)
    if test_naming:
        user_input_obj["test_naming_convention"] = test_naming

    # Detect repo's test location convention (co-located, __tests__, separate dir)
    # Skip auto-detection if user explicitly configured test file location
    # Cross-ref: website repo app/dashboard/rules/config/structured-rules.ts testFileLocation options
    structured_rules = repo_settings.get("structured_rules") if repo_settings else None
    explicit_location = None
    if isinstance(structured_rules, dict):
        test_file_location = structured_rules.get("testFileLocation")
        if test_file_location and test_file_location != "Auto-detect from repo":
            explicit_location = test_file_location
    if explicit_location:
        user_input_obj["test_location_convention"] = explicit_location
        logger.info("Using explicit test location setting: %s", explicit_location)
    else:
        test_location = detect_test_location_convention(clone_dir)
        if test_location:
            user_input_obj["test_location_convention"] = test_location

    user_input = dumps(user_input_obj)
    messages: list[MessageParam] = [{"role": "user", "content": user_input}]
    if impl_file_content:
        formatted_impl = format_content_with_line_numbers(
            file_path=impl_file_path, content=impl_file_content
        )
        messages.append({"role": "user", "content": formatted_impl})
    for path, content in test_files.items():
        messages.append({"role": "user", "content": content})
    for path, content in reference_files.items():
        if path == impl_file_path:
            continue
        messages.append({"role": "user", "content": content})

    # Validate files for syntax issues before editing
    files_to_validate = list(
        {impl_file_path, *reference_files.keys(), *test_files.keys()}
    )
    validation_result = await verify_task_is_ready(
        base_args=base_args,
        file_paths=files_to_validate,
        run_phpunit=False,
    )
    base_args["baseline_tsc_errors"] = set(validation_result.tsc_errors)
    pre_existing_errors = ""
    if validation_result.errors:
        pre_existing_errors = "\n".join(validation_result.errors)
        logger.warning("Remaining errors:\n%s", pre_existing_errors)
    fixes_applied = validation_result.fixes_applied

    # If uncovered code is dead or untestable, notify agent with category-specific action
    if untestable_code_info and untestable_code_info.result:
        if untestable_code_info.category == "dead_code":
            untestable_msg = (
                f"DEAD CODE detected in `{impl_file_path}`: {untestable_code_info.reason}\n\n"
                "ACTION REQUIRED: REMOVE this dead/unreachable code entirely (e.g., use optional chaining, remove redundant guards). "
                "Do NOT use istanbul ignore or coverage exclusion comments. Dead code must be deleted, not excluded."
            )
        else:
            untestable_msg = (
                f"Genuinely untestable code detected in `{impl_file_path}`: {untestable_code_info.reason}\n\n"
                "This code is reachable at runtime but untestable due to framework limitations. "
                "You may use coverage exclusion comments (istanbul ignore / pragma: no cover) with a reason explaining why."
            )
        messages.append({"role": "user", "content": untestable_msg})
        logger.info(
            "Added %s message for %s", untestable_code_info.category, impl_file_path
        )

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
    completion_reason = ""

    system_message = create_system_message(
        trigger=trigger, repo_settings=repo_settings, clone_dir=clone_dir
    )

    for _iteration in range(MAX_ITERATIONS):
        if should_bail(
            current_time=current_time,
            phase="pr processing",
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
            model_id=model_id,
        )
        messages = result.messages
        is_completed = result.is_completed
        completion_reason = result.completion_reason
        p = result.p
        total_token_input += result.token_input
        total_token_output += result.token_output
        if is_completed:
            logger.info(
                "Agent signaled completion via verify_task_is_complete, breaking loop"
            )
            break

        # Force GC between rounds to free temporary objects (messages, diffs) and reduce Lambda OOM risk
        gc_collect_and_log()

    # Log if loop exhausted without completion and force verification
    if not is_completed:
        logger.warning(
            "Agent loop hit MAX_ITERATIONS (%d) without calling verify_task_is_complete. Forcing verification.",
            MAX_ITERATIONS,
        )
        await verify_task_is_complete(base_args=base_args)

    # Add headers to test files before triggering CI
    changed_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )

    for file_change in changed_files:
        file_path = file_change["filename"]
        if not is_test_file(file_path) or is_config_file(file_path):
            continue

        file_content = read_local_file(file_path=file_path, base_dir=clone_dir)
        if not file_content:
            continue

        updated_content = merge_test_file_headers(file_content, file_path)
        if not updated_content or updated_content == file_content:
            continue

        write_and_commit_file(
            file_content=updated_content,
            file_path=file_path,
            base_args=base_args,
            commit_message=f"Disable unnecessary lint rules for {file_path}",
        )

    # Trigger final test workflows with an empty commit
    comment_body = "Triggering workflows..."
    p += 5
    add_log_message(comment_body, log_messages)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )
    create_empty_commit(base_args=base_args)

    # Update the PR comment
    body_after_pr = build_pr_completion_comment(
        pr_creator=pr_creator,
        sender_name=sender_name,
        trigger=trigger,
    )
    update_comment(body=body_after_pr, base_args=base_args)

    # Update PR body with Claude-generated summary of what GA did
    agent_comments = get_comments(
        pr_number=pr_number, base_args=base_args, includes_me=True
    )
    pr_body_summary = generate_and_upsert_pr_body_section(
        owner_name=owner_name,
        repo_name=repo_name,
        pr_number=pr_number,
        token=token,
        current_body=pr_body,
        trigger=trigger,
        context={
            "pr_title": pr_title,
            "changed_files": changed_files,
            "completion_reason": completion_reason,
            "agent_comments": agent_comments,
        },
        usage_id=usage_id,
    )

    if pr_body_summary:
        slack_notify(pr_body_summary, thread_ts)

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

    # Check if user just ran out of credits and send casual notification (deduplicated per owner)
    if billing_type == "credit":
        owner = get_owner(owner_id=owner_id)
        if owner and owner["credit_balance_usd"] <= 0 and sender_id:
            is_new = insert_email_send(
                owner_id=owner_id, owner_name=owner_name, email_type="credits_depleted"
            )
            if is_new is not False:
                user = get_user(user_id=sender_id)
                email = user.get("email") if user else None
                if email:
                    subject, text = get_credits_depleted_email_text(sender_name)
                    result = send_email(to=email, subject=subject, text=text)
                    if result and result.get("id"):
                        update_email_send(
                            owner_id=owner_id,
                            email_type="credits_depleted",
                            resend_email_id=result["id"],
                        )

    # End notification
    status = "Completed" if is_completed else "<!channel> Failed"
    end_msg = f"{status}: {owner_name}/{repo_name} {pr_url}"
    slack_notify(end_msg, thread_ts)
    return
