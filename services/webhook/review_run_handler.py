# Standard imports
from datetime import datetime
import json
from pathlib import Path
import time

# Third-party imports
from anthropic.types import MessageParam

# Local imports
from config import GITHUB_APP_USER_NAME, PRODUCT_ID
from constants.agent import COST_CAP_RATIO, MAX_ITERATIONS
from constants.triggers import ReviewTrigger
from payloads.github.pull_request_review_comment.types import ReviewComment
from services.github.types.webhook.review_run_payload import ReviewRunPayload
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.agents.verify_task_is_ready import verify_task_is_ready
from services.aws.s3.refresh_mongodb_cache import refresh_mongodb_cache
from services.chat_with_agent import chat_with_agent
from services.node.ensure_node_packages import ensure_node_packages
from services.node.set_npm_token_env import set_npm_token_env
from services.php.ensure_php_packages import ensure_php_packages
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.clone_repo_and_install_dependencies import (
    clone_repo_and_install_dependencies,
)
from services.git.git_merge_base_into_pr import git_merge_base_into_pr
from services.github.comments.create_comment import create_comment
from services.github.comments.get_pr_comments import get_pr_comments
from services.github.commits.get_head_commit_count_behind_base import (
    get_head_commit_count_behind_base,
)
from services.github.comments.reply_to_comment import reply_to_comment
from services.github.comments.update_comment import update_comment
from services.slack.slack_notify import slack_notify
from services.supabase.credits.check_purchase_exists import check_purchase_exists
from services.supabase.webhook_deliveries.insert_webhook_delivery import (
    insert_webhook_delivery,
)
from services.supabase.credits.get_credit_price import get_credit_price
from services.git.create_empty_commit import create_empty_commit
from services.git.get_reference import get_reference
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.pulls.get_review_inline_comments import get_review_inline_comments
from services.github.pulls.get_review_summary_comment import get_review_summary_comment
from services.github.pulls.get_review_thread_comments import get_review_thread_comments
from services.github.token.get_installation_token import get_installation_access_token
from services.github.users.get_email_from_commits import get_email_from_commits
from services.github.users.get_user_public_email import get_user_public_info
from services.claude.tools.tools import TOOLS_FOR_REVIEW_COMMENTS
from services.github.comments.update_progress import update_progress
from services.supabase.create_user_request import create_user_request
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.update_usage import update_usage
from services.types.base_args import ReviewBaseArgs
from services.webhook.utils.create_system_message import create_system_message
from services.webhook.utils.get_preferred_model import get_preferred_model
from services.webhook.utils.should_bail import should_bail
from utils.files.read_local_file import read_local_file
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.files.get_local_file_tree import get_local_file_tree
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger
from utils.memory.gc_collect_and_log import gc_collect_and_log
from utils.progress_bar.progress_bar import create_progress_bar


async def handle_review_run(
    payload: ReviewRunPayload,
    trigger: ReviewTrigger,
    lambda_info: dict[str, str | None] | None = None,
):
    current_time = time.time()
    # Extract comment fields
    review = payload["comment"]
    review_id = review["id"]
    review_node_id = review["node_id"]
    review_body = review["body"]
    review_author = review["user"]
    review_author_is_bot = review_author["type"] == "Bot"
    review_path = review["path"]
    review_subject_type = review["subject_type"]
    review_line = review["line"]
    review_side = review["side"]

    # Extract repository related variables
    repo = payload["repository"]
    repo_id = repo["id"]
    repo_name = repo["name"]
    is_fork = repo["fork"]

    # Extract owner related variables
    owner = repo["owner"]
    owner_type = owner["type"]
    owner_id = owner["id"]
    owner_name = owner["login"]
    set_npm_token_env(owner_id)

    # Extract PR related variables
    pull_request = payload["pull_request"]
    pr_number = pull_request["number"]
    pr_title = pull_request["title"]
    pr_body = pull_request["body"]
    pr_url = pull_request["url"]
    pr_file_url = f"{pr_url}/files"
    base_branch = pull_request["base"]["ref"]  # main, master, etc.
    head_branch = pull_request["head"]["ref"]  # gitauto/dashboard-20250101-155924-Ab1C
    pr_creator = pull_request["user"]["login"]
    if not head_branch.startswith(PRODUCT_ID + "/"):
        logger.info(
            "Ignoring review comment on non-GitAuto PR (branch: %s)", head_branch
        )
        return

    # Extract sender related variables and return if sender is GitAuto itself
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]
    if sender_name == GITHUB_APP_USER_NAME:
        logger.info("Ignoring review comment from GitAuto itself")
        return

    # Check if review comment trigger is enabled for this repo
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_review_comment"):
        logger.info("trigger_on_review_comment is disabled, skipping")
        return

    has_purchased = check_purchase_exists(owner_id=owner_id)
    model_id = get_preferred_model(
        repo_settings=repo_settings,
        is_paid=has_purchased,
    )

    # Extract other information
    installation_id: int = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)
    sender_info = get_user_public_info(username=sender_name, token=token)
    if not sender_info.email:
        logger.info(
            "Sender %s has no public email; falling back to commit-author email lookup",
            sender_name,
        )
        email = get_email_from_commits(
            owner=owner_name, repo=repo_name, username=sender_name, token=token
        )
        if email:
            logger.info(
                "Recovered email for sender %s from commit authors", sender_name
            )
            sender_info.email = email

    # Fetch review summary body if this inline comment is part of a review
    review_summary = ""
    pull_request_review_id = review.get("pull_request_review_id")
    if pull_request_review_id:
        logger.info(
            "Inline comment belongs to review_id=%s; fetching top-level review summary",
            pull_request_review_id,
        )
        summary_body = get_review_summary_comment(
            owner=owner_name,
            repo=repo_name,
            pr_number=pr_number,
            review_id=pull_request_review_id,
            token=token,
        )
        if summary_body and summary_body.strip():
            logger.info(
                "Attaching review summary (%d chars) from review_id=%s to agent context",
                len(summary_body),
                pull_request_review_id,
            )
            review_summary = summary_body

    # Batch: when a reviewer (e.g. Devin) submits a review with N inline comments, GitHub fires N webhooks. Without dedup, each triggers a separate Lambda that races to push, wasting tokens. Only one invocation wins the lock; it sleeps, fetches all comments, and handles them in one session.
    review_inline_comments: list[ReviewComment] = []
    if pull_request_review_id and trigger == "pr_file_review":
        dedup_key = f"review-dedup-{repo_id}-{pr_number}-{pull_request_review_id}"
        inserted = insert_webhook_delivery(
            delivery_id=dedup_key, event_name="pr_file_review_dedup"
        )
        if inserted is False:
            logger.info(
                "Another invocation handling review_id=%d for PR #%d, skipping",
                pull_request_review_id,
                pr_number,
            )
            return

        # Real data: Devin review_id 4117870568 on SpiderPlus PR #13871 (2026-04-16) had 4 inline comments created 01:57:24–01:57:32 UTC but submitted together at 01:57:33 — GitHub webhooks fire at submission (~1s apart). 10s gives ample headroom including Lambda cold starts.
        time.sleep(10)
        review_inline_comments = (
            get_review_inline_comments(
                owner=owner_name,
                repo=repo_name,
                pr_number=pr_number,
                review_id=pull_request_review_id,
                token=token,
            )
            or []
        )
        logger.info(
            "Won batch dedup lock for review_id=%d; fetched %d inline comments after 10s sibling wait",
            pull_request_review_id,
            len(review_inline_comments),
        )

    # Get list of changed files in the PR (used for bot relevance check and later for file processing)
    pr_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )

    # Build review_comment based on multiple review inline comments, PR-level, or single inline comment
    if review_inline_comments:
        logger.info(
            "Building combined review_comment from %d review inline comments",
            len(review_inline_comments),
        )
        parts = [f"## Review with {len(review_inline_comments)} inline comments\n"]
        for i, rc in enumerate(review_inline_comments, 1):
            rc_path = rc.get("path", "")
            rc_line = rc.get("line", "?")
            rc_body = rc.get("body", "")
            parts.append(f"### Comment {i}: `{rc_path}` Line {rc_line}\n{rc_body}\n")
        review_comment = "\n".join(parts)
    elif not review_path:
        logger.info(
            "PR-level review comment (no file path) on PR #%s; applying bot-relevance filter",
            pr_number,
        )
        # For PR-level comments (no file path), check bot relevance and loop prevention
        if review_author_is_bot:
            logger.info(
                "PR-level comment from bot %s; checking if it references any of the PR's changed files",
                review_author["login"],
            )
            # Check if bot comment mentions any PR file paths (skip irrelevant bot comments like Security Hub scans)
            pr_file_paths = [f["filename"] for f in pr_files]
            mentions_pr_file = any(path in review_body for path in pr_file_paths)
            if not mentions_pr_file:
                logger.info(
                    "Ignoring bot PR comment from %s - does not mention any PR file paths: %s",
                    review_author["login"],
                    pr_file_paths,
                )
                return
        review_comment = review_body
    else:
        logger.info(
            "Inline review comment on %s:%s; fetching full thread for context",
            review_path,
            review_line,
        )
        # Get all comments in the review thread
        thread_result = get_review_thread_comments(
            owner=owner_name,
            repo=repo_name,
            pr_number=pr_number,
            comment_node_id=review_node_id,
            token=token,
        )
        thread_comments = thread_result.comments

        # Skip if the review thread is already resolved
        if thread_result.is_resolved:
            logger.info("Ignoring review comment on already-resolved thread")
            return

        # If a bot posted this comment AND GitAuto already replied in the same thread, skip to prevent infinite bot-to-bot loops. But if GitAuto hasn't replied yet, process it (e.g. Devin's first review comment is valuable feedback).
        if review_author_is_bot and thread_comments:
            logger.info(
                "Inline comment from bot %s in an existing thread; checking whether GitAuto already replied to avoid bot-to-bot loop",
                review_author["login"],
            )
            gitauto_already_replied = any(
                c["author"]["login"] == GITHUB_APP_USER_NAME for c in thread_comments
            )
            if gitauto_already_replied:
                logger.info(
                    "Ignoring bot review comment from %s - GitAuto already replied in this thread",
                    review_author["login"],
                )
                return

        # Combine all comments in chronological order for context
        review_comment = f"## Review thread on {review_path} Line: {review_line}\n"
        if thread_comments:
            logger.info(
                "Assembling review_comment from %d thread messages on %s:%s",
                len(thread_comments),
                review_path,
                review_line,
            )
            for tc in thread_comments:
                author = tc["author"]["login"]
                body = tc["body"]
                created_at = tc["createdAt"]
                review_comment += f"{author} commented at {created_at}: {body}\n"
        else:
            logger.warning(
                "Thread fetch returned empty comments for %s:%s; falling back to single review body",
                review_path,
                review_line,
            )
            # Fallback to single comment if thread fetch fails
            review_comment += f"{review_body}"

    # Start notification
    start_msg = f"Review handler started: `{trigger}` by `{sender_name}` for `{pr_number}:{pr_title}` in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)
    if not review_author_is_bot:
        logger.info(
            "Human reviewer on PR #%s; mentioning channel with reviewer display name in Slack thread",
            pr_number,
        )
        display_name = sender_info.display_name or sender_name
        slack_notify(f"<!channel> {display_name}: {review_body}", thread_ts)

    # Create the usage row up front so base_args carries a real usage_id and every downstream LLM call attributes cost correctly.
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
        email=sender_info.email,
        display_name=sender_info.display_name,
        lambda_info=lambda_info,
    )

    clone_dir = get_clone_dir(owner_name, repo_name, pr_number)
    base_args: ReviewBaseArgs = {
        # Required fields
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": get_clone_url(owner_name, repo_name, token),
        "is_fork": is_fork,
        "pr_number": pr_number,
        "pr_comments": [
            f"@{c['user']['login']} ({c['created_at']}): {c['body']}"
            for c in get_pr_comments(
                owner=owner_name,
                repo=repo_name,
                pr_number=pr_number,
                token=token,
                exclude_self=True,
            )
        ],
        "latest_commit_sha": pull_request["head"]["sha"],
        "base_branch": base_branch,
        "new_branch": head_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": sender_info.email,
        "sender_display_name": sender_info.display_name,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "clone_dir": clone_dir,
        "pr_title": pr_title,
        "pr_body": pr_body or "",
        "pr_creator": pr_creator,
        "pr_url": pr_url,
        "pr_file_url": pr_file_url,
        "review_id": review_id,
        "review_path": review_path,
        "review_subject_type": review_subject_type,
        "review_line": review_line,
        "review_side": review_side,
        # "review_position": review_position,
        "review_body": review_body,
        "review_comment": review_comment,
        "model_id": model_id,
        "verify_consecutive_failures": 0,
        "quality_gate_fail_count": 0,
        "usage_id": usage_id,
        "trigger": trigger,
        "skip_ci": True,
        "slack_thread_ts": thread_ts,
    }

    # Clone repo to tmp
    clone_repo_and_install_dependencies(
        owner=owner_name,
        repo=repo_name,
        base_branch=base_branch,
        pr_branch=head_branch,
        token=token,
        clone_dir=clone_dir,
    )

    # Fire-and-forget: refresh mongodb-binaries on S3 for the next run
    refresh_mongodb_cache(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        clone_dir=clone_dir,
    )

    # Webhook payload doesn't include mergeable_state, so fetch the full PR from REST API
    full_pr = get_pull_request(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )
    mergeable_state = full_pr.get("mergeable_state") if full_pr else None
    if mergeable_state == "dirty":
        logger.info("Merging base branch, mergeable_state=%s", mergeable_state)
        behind_by = get_head_commit_count_behind_base(
            owner=owner_name,
            repo=repo_name,
            base=base_branch,
            head=head_branch,
            token=token,
        )
        git_merge_base_into_pr(
            clone_dir=clone_dir, base_branch=base_branch, behind_by=behind_by
        )
    else:
        logger.info("Skipping merge, mergeable_state=%s", mergeable_state)

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

    # Greeting and progress tracking (skip for bots to avoid triggering bot-to-bot noise)
    p = 0
    log_messages: list[str] = []
    if not review_author_is_bot:
        logger.info("Posting greeting comment for human reviewer")
        msg = "Thanks for the feedback. I'm on it."
        add_log_message(msg, log_messages)
        comment_body = create_progress_bar(p=0, msg="\n".join(log_messages))
        if review_path:
            logger.info("Replying inline to review comment on %s", review_path)
            comment_url = reply_to_comment(base_args=base_args, body=comment_body)
        else:
            logger.info("Creating top-level PR comment for review_id=%s", review_id)
            original_url = f"https://github.com/{owner_name}/{repo_name}/pull/{pr_number}#issuecomment-{review_id}"
            mention = f"@{sender_name}'s " if not review_author_is_bot else ""
            linked_body = f"Re: {mention}[comment]({original_url})\n\n{comment_body}"
            comment_url = create_comment(base_args=base_args, body=linked_body)
        base_args["comment_url"] = comment_url
    else:
        logger.info("Skipping greeting comment for bot reviewer %s", sender_name)

    # Get review commented file(s) — stored as separate messages (not inside JSON) so remove_outdated_messages() can find and replace them when agent re-reads.
    review_file_messages: list[MessageParam] = []
    if review_inline_comments:
        logger.info(
            "Reading files for %d review inline comments", len(review_inline_comments)
        )
        unique_paths: list[str] = list(
            dict.fromkeys(
                str(rc.get("path")) for rc in review_inline_comments if rc.get("path")
            )
        )
        for fp in unique_paths:
            raw = read_local_file(file_path=fp, base_dir=clone_dir)
            if raw:
                logger.info("Read review inline comment file %s", fp)
                formatted = format_content_with_line_numbers(file_path=fp, content=raw)
                review_file_messages.append({"role": "user", "content": formatted})
            else:
                logger.info("Batched file %s not found or empty", fp)
        if not review_author_is_bot:
            logger.info(
                "Reporting file-read progress to human reviewer on PR #%s", pr_number
            )
            p = update_progress(
                msg=f"Read {len(unique_paths)} files from review comments.",
                p=p,
                log_messages=log_messages,
                base_args=base_args,
            )
        else:
            logger.info(
                "Skipping progress update for bot reviewer (review inline comments)"
            )
    elif review_path:
        logger.info("Reading single review file %s", review_path)
        raw = read_local_file(file_path=review_path, base_dir=clone_dir)
        if raw:
            logger.info("Read review file %s", review_path)
            formatted = format_content_with_line_numbers(
                file_path=review_path, content=raw
            )
            review_file_messages.append({"role": "user", "content": formatted})
        else:
            logger.info("Review file %s not found or empty", review_path)
        if not review_author_is_bot:
            logger.info(
                "Reporting single-file read progress to human reviewer on PR #%s",
                pr_number,
            )
            p = update_progress(
                msg=f"Read the file `{review_path}` you commented on.",
                p=p,
                log_messages=log_messages,
                base_args=base_args,
            )
        else:
            logger.info("Skipping progress update for bot reviewer (single file)")
    else:
        logger.info("No review file path — PR-level comment, skipping file read")

    if not review_author_is_bot:
        logger.info(
            "Reporting changed-files count (%d) to human reviewer on PR #%s",
            len(pr_files),
            pr_number,
        )
        p = update_progress(
            msg=f"Found {len(pr_files)} changed files in the PR.",
            p=p,
            log_messages=log_messages,
            base_args=base_args,
        )

    # Validate files for syntax issues before editing
    files_to_validate = [f["filename"] for f in pr_files if f["status"] != "removed"]
    validation_result = await verify_task_is_ready(
        base_args=base_args,
        file_paths=files_to_validate,
        run_phpunit=False,
    )
    base_args["baseline_tsc_errors"] = set(validation_result.tsc_errors)
    pre_existing_errors = ""
    if validation_result.errors:
        pre_existing_errors = "\n".join(validation_result.errors)
        logger.warning(
            "Pre-existing validation errors on PR #%s before edits begin (%d):\n%s",
            pr_number,
            len(validation_result.errors),
            pre_existing_errors,
        )
    fixes_applied = validation_result.fixes_applied

    # Get repository settings
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")

    root_files = get_local_file_tree(base_args=base_args, dir_path="")
    target_dir: str | None = None
    target_dir_files: list[str] = []
    if review_path:
        logger.info(
            "Narrowing agent scope to parent dir of review_path=%s", review_path
        )
        parent = str(Path(review_path).parent)
        if parent != ".":
            logger.info(
                "Setting target_dir=%s for agent scope on PR #%s", parent, pr_number
            )
            target_dir = parent
            target_dir_files = get_local_file_tree(base_args=base_args, dir_path=parent)

    input_message = {
        "step_1_review_comment": review_comment,
        "pull_request_title": pr_title,
        "pull_request_body": pr_body,
        "pr_files": pr_files,
        "today": today,
        "root_files": root_files,
        "target_dir": target_dir,
        "target_dir_files": target_dir_files,
    }
    if review_summary:
        logger.info(
            "Attaching review_summary (%d chars) to input_message", len(review_summary)
        )
        input_message["review_summary"] = review_summary
    if fixes_applied or pre_existing_errors:
        logger.info(
            "Prettier/ESLint auto-fix ran before agent; attaching note to input_message"
        )
        input_message["step_2_prettier_eslint_note"] = (
            "Before you start, we ran Prettier/ESLint --fix. "
            "Files may have changed. Read the latest content."
        )
    if fixes_applied:
        logger.info("Attaching step_2a auto-fixed list to input_message")
        input_message["step_2a_auto_fixed_and_committed"] = fixes_applied
    if pre_existing_errors:
        logger.info("Attaching step_2b pre-existing unfixable errors to input_message")
        input_message["step_2b_remaining_unfixable_errors"] = pre_existing_errors
    user_input = json.dumps(obj=input_message)

    # Create messages — file content in separate messages for remove_outdated_messages()
    messages: list[MessageParam] = [{"role": "user", "content": user_input}]
    messages.extend(review_file_messages)

    # Loop a process explore repo and commit changes until the ticket is resolved
    total_token_input = 0
    total_token_output = 0
    is_completed = False
    completion_reason = ""

    system_message = create_system_message(
        trigger=trigger, repo_settings=repo_settings, clone_dir=clone_dir
    )

    cost_cap_usd = get_credit_price(model_id) * COST_CAP_RATIO
    concurrent_push_detected = False

    for iteration in range(MAX_ITERATIONS):
        logger.info(
            "Agent loop iteration %d/%d on PR #%s",
            iteration + 1,
            MAX_ITERATIONS,
            pr_number,
        )
        if should_bail(
            current_time=current_time,
            phase="execution",
            base_args=base_args,
            slack_thread_ts=thread_ts,
            cost_cap_usd=cost_cap_usd,
        ):
            logger.info(
                "Breaking agent loop on PR #%s: should_bail() tripped (timeout or cost cap)",
                pr_number,
            )
            break

        # Re-check trigger_on_review_comment in case it was disabled during execution
        refreshed_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
        if not refreshed_settings or not refreshed_settings.get(
            "trigger_on_review_comment"
        ):
            logger.info(
                "Review-comment trigger disabled mid-execution on PR #%s; breaking",
                pr_number,
            )
            is_completed = True
            completion_reason = "Stopped because the review comment trigger was disabled during execution."
            break

        # Check if the review thread was resolved while we were working
        if review_path:
            logger.info(
                "Re-checking resolution state of review thread on PR #%s during loop",
                pr_number,
            )
            thread_check = get_review_thread_comments(
                owner=owner_name,
                repo=repo_name,
                pr_number=pr_number,
                comment_node_id=review_node_id,
                token=token,
            )
            if thread_check.is_resolved:
                logger.info("Review thread was resolved during execution, stopping")
                break

        # Call the agent to explore the codebase and commit changes
        result = await chat_with_agent(
            messages=messages,
            system_message=system_message,
            base_args=base_args,
            p=p,
            log_messages=log_messages,
            usage_id=usage_id,
            tools=TOOLS_FOR_REVIEW_COMMENTS,
            model_id=model_id,
        )
        messages = result.messages
        is_completed = result.is_completed
        completion_reason = result.completion_reason
        p = result.p
        total_token_input += result.token_input
        total_token_output += result.token_output

        if result.concurrent_push_detected:
            logger.warning(
                "review_run: concurrent push on PR #%s; breaking agent loop",
                pr_number,
            )
            concurrent_push_detected = True
            completion_reason = f"Another commit landed on `{base_args['new_branch']}` while I was handling your review. Their push triggers CI on its own, so I'm stopping here — your push stands."
            break

        if is_completed:
            logger.info(
                "Agent signaled completion via verify_task_is_complete, breaking loop"
            )
            break

        # Force GC between rounds to free temporary objects (messages, diffs) and reduce Lambda OOM risk
        gc_collect_and_log()

    # Log if loop exhausted without completion and force verification (skip when a concurrent push was detected — verifying on stale state would re-trigger the same bail)
    if not is_completed and not concurrent_push_detected:
        logger.warning(
            "Agent loop hit MAX_ITERATIONS (%d) without calling verify_task_is_complete. Forcing verification.",
            MAX_ITERATIONS,
        )
        final_result = await verify_task_is_complete(base_args=base_args)
        is_completed = final_result.success

    # Trigger final test workflows with an empty commit (skip if agent made no commits, or if concurrent push already advances CI)
    if concurrent_push_detected:
        logger.info(
            "review_run: skipping final empty commit on PR #%s — racer's push triggers CI on its own",
            pr_number,
        )
    else:
        logger.info(
            "review_run: checking whether agent made commits to warrant a final empty commit on PR #%s",
            pr_number,
        )
        current_head = get_reference(
            clone_url=base_args["clone_url"], branch=base_args["new_branch"]
        )
        if current_head != pull_request["head"]["sha"]:
            logger.info(
                "Agent made commits on %s (head changed from %s to %s); retriggering CI with empty commit",
                base_args["new_branch"],
                pull_request["head"]["sha"],
                current_head,
            )
            if not review_author_is_bot:
                logger.info(
                    "Informing human reviewer on PR #%s about final empty commit",
                    pr_number,
                )
                update_comment(
                    body="Creating final empty commit to trigger workflows...",
                    base_args=base_args,
                )
            pushed = create_empty_commit(base_args=base_args)
            if not pushed and not review_author_is_bot:
                logger.warning(
                    "Empty commit skipped on %s: concurrent push detected",
                    base_args["new_branch"],
                )
                update_comment(
                    body=f"Another commit landed on `{base_args['new_branch']}` while I was working. Their push triggers CI on its own, so no empty commit needed.",
                    base_args=base_args,
                )

    # Use the agent's own explanation as the final reply, or a fallback if empty
    if not completion_reason:
        completion_reason = (
            "Done." if is_completed else "I was unable to complete this task."
        )
        logger.warning(
            "Agent returned empty completion_reason for PR #%s; using fallback: %s",
            pr_number,
            completion_reason,
        )
    if not review_path:
        logger.info(
            "PR-level review on PR #%s; posting completion_reason as a new comment",
            pr_number,
        )
        create_comment(base_args=base_args, body=completion_reason)
    elif review_author_is_bot:
        logger.info(
            "Inline review from bot %s on %s; replying in the same thread",
            review_author["login"],
            review_path,
        )
        reply_to_comment(base_args=base_args, body=completion_reason)
    else:
        logger.info(
            "Inline review from human on %s; updating existing progress comment on PR #%s",
            review_path,
            pr_number,
        )
        update_comment(body=completion_reason, base_args=base_args)

    # Update usage record
    end_time = time.time()
    if usage_id:
        logger.info(
            "Finalizing usage_id=%s for PR #%s: tokens_in=%d tokens_out=%d",
            usage_id,
            pr_number,
            total_token_input,
            total_token_output,
        )
        update_usage(
            usage_id=usage_id,
            token_input=total_token_input,
            token_output=total_token_output,
            total_seconds=int(end_time - current_time),
            pr_number=pr_number,
            is_completed=True,
        )

    # End notification
    end_msg = "Completed" if is_completed else "<!channel> Failed"
    slack_notify(end_msg, thread_ts)
    logger.info(
        "review_run_handler returning for PR #%s; is_completed=%s",
        pr_number,
        is_completed,
    )
    return
