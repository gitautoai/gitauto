# Standard imports
import logging
from datetime import datetime, timezone
from typing import cast

# Local imports (Types)
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from schemas.supabase.types import Coverages, CoveragesInsert

# Local imports (AWS)
from services.aws.delete_scheduler import delete_scheduler

# Local imports (GitHub)
from services.github.branches.get_default_branch import get_default_branch
from services.github.files.get_raw_content import get_raw_content
from services.github.issues.create_issue import create_issue
from services.github.pulls.get_open_pull_requests import get_open_pull_requests
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree import get_file_tree

# Local imports (Notifications)
from services.resend.send_email import send_email
from services.resend.text.issues_disabled_email import get_issues_disabled_email_text
from services.slack.slack_notify import slack_notify

# Local imports (Supabase)
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.supabase.coverages.insert_coverages import insert_coverages
from services.supabase.coverages.update_issue_url import update_issue_url
from services.supabase.repositories.get_repository import get_repository
from services.supabase.repositories.update_repository import update_repository
from services.supabase.users.get_user import get_user
from services.stripe.check_availability import check_availability

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_migration_file import is_migration_file
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file
from utils.files.should_skip_test import should_skip_test
from utils.files.should_test_file import should_test_file
from utils.issue_templates.schedule import get_issue_title, get_issue_body


@handle_exceptions(raise_on_error=True)
def schedule_handler(event: EventBridgeSchedulerEvent):
    # Extract details from the event payload
    owner_id = event.get("ownerId")
    owner_type = event.get("ownerType")
    owner_name = event.get("ownerName")
    repo_id = event.get("repoId")
    repo_name = event.get("repoName")
    user_id = event.get("userId")
    user_name = event.get("userName")
    installation_id = event.get("installationId")

    if not all(
        [
            owner_id,
            owner_name,
            owner_type,
            repo_id,
            repo_name,
            user_id,
            user_name,
            installation_id,
        ]
    ):
        raise ValueError("Missing required fields in event detail")

    # Get installation access token - simplified since we already have installation_id
    token = get_installation_access_token(installation_id=installation_id)
    if token is None:
        # Delete scheduler since installation is invalid
        schedule_name = f"gitauto-repo-{owner_id}-{repo_id}"
        delete_scheduler(schedule_name)
        msg = f"Installation {installation_id} no longer exists. Cleaned up scheduler."
        logging.info(msg)
        return {"status": "skipped", "message": msg}

    # Get repository settings - check if trigger_on_schedule is enabled
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_schedule"):
        msg = f"Skipping repo_id: {repo_id} - trigger_on_schedule is not enabled"
        logging.info(msg)
        return {"status": "skipped", "message": msg}

    # Check availability
    availability_status = check_availability(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        installation_id=installation_id,
        sender_name=user_name,
    )

    if not availability_status["can_proceed"]:
        return {"status": "skipped", "message": availability_status["log_message"]}

    # Get repository files and coverage data
    default_branch, _ = get_default_branch(
        owner=owner_name, repo=repo_name, token=token
    )
    tree_items = get_file_tree(
        owner=owner_name, repo=repo_name, ref=default_branch, token=token
    )

    # Extract necessary data
    all_files_with_sizes = [
        (item["path"], item.get("size", 0))
        for item in tree_items
        if item["type"] == "blob"  # Only files
    ]

    all_coverages = get_all_coverages(owner_id=owner_id, repo_id=repo_id)

    # all_files LEFT JOIN all_coverages
    enriched_all_files: list[Coverages] = []
    for file_path, file_size in all_files_with_sizes:
        coverages = next(
            (c for c in all_coverages if c["full_path"] == file_path), None
        )
        if coverages:
            coverages["file_size"] = file_size
            enriched_all_files.append(coverages)
        else:
            new_coverage: Coverages = {
                "id": 0,
                "full_path": file_path,
                "owner_id": owner_id,
                "repo_id": repo_id,
                "branch_name": default_branch,
                "created_by": user_name,
                "updated_by": user_name,
                "level": "file",
                "file_size": file_size,
                "statement_coverage": 0,
                "function_coverage": 0,
                "branch_coverage": 0,
                "line_coverage": 0,
                "path_coverage": 0,
                "package_name": None,
                "language": None,
                "github_issue_url": None,
                "is_excluded_from_testing": False,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            enriched_all_files.append(new_coverage)

    if not enriched_all_files:
        msg = f"No files found for {owner_name}/{repo_name}"
        logging.info(msg)
        return {"status": "skipped", "message": msg}

    # Filter out files with 100% coverage in all three metrics
    files_needing_tests = [
        item
        for item in enriched_all_files
        if not (
            cast(float, item["statement_coverage"]) == 100.0
            and cast(float, item["function_coverage"]) == 100.0
            and cast(float, item["branch_coverage"]) == 100.0
        )
    ]

    # Sort: prioritize untouched files (0% coverage) first, then by file_size, coverage, path
    files_needing_tests.sort(
        key=lambda x: (
            1 if cast(float, x["statement_coverage"]) > 0 else 0,
            cast(int, x["file_size"]),
            cast(float, x["statement_coverage"]),
            cast(str, x["full_path"]),
        )
    )

    # Get open PRs once before the loop
    open_prs = get_open_pull_requests(
        owner=owner_name, repo=repo_name, target_branch=default_branch, token=token
    )

    # Find the first suitable file from sorted list
    target_item = None
    for item in files_needing_tests:
        item_path = cast(str, item["full_path"])

        # Skip non-code files
        if not is_code_file(item_path):
            continue

        # Skip test files
        if is_test_file(item_path):
            continue

        # Skip types files
        if is_type_file(item_path):
            continue

        # Skip migration files
        if is_migration_file(item_path):
            continue

        # Skip files that only contain exports/re-exports or are empty
        content = get_raw_content(
            owner=owner_name,
            repo=repo_name,
            file_path=item_path,
            ref=default_branch,
            token=token,
        )
        # Skip empty files or files with only whitespace
        if not content or not content.strip():
            continue

        # Skip files that should be skipped based on content
        if should_skip_test(item_path, content):
            continue

        # Skip files excluded from testing
        if item.get("is_excluded_from_testing"):
            continue

        # Skip files that have open PRs
        if any(item_path in pr.get("title", "") for pr in open_prs):
            continue

        # Final check: Use Claude AI to determine if this file should be tested (expensive, so run last)
        if not should_test_file(item_path, content):
            continue

        # Found the best suitable file
        target_item = item
        break

    if target_item is None:
        msg = f"No suitable file found for {owner_name}/{repo_name}"
        logging.info(msg)
        return {"status": "skipped", "message": msg}

    target_path = target_item["full_path"]

    # Create issue title and body
    statement_coverage = target_item["statement_coverage"]
    has_existing_tests = statement_coverage is not None and statement_coverage > 0
    title = get_issue_title(target_path, has_existing_tests=has_existing_tests)
    body = get_issue_body(
        owner=owner_name,
        repo=repo_name,
        branch=default_branch,
        file_path=target_path,
        statement_coverage=target_item["statement_coverage"],
        function_coverage=target_item["function_coverage"],
        branch_coverage=target_item["branch_coverage"],
        line_coverage=target_item["line_coverage"],
        uncovered_lines=target_item["uncovered_lines"],
        uncovered_functions=target_item["uncovered_functions"],
        uncovered_branches=target_item["uncovered_branches"],
    )

    # Create the issue with gitauto label and assign to the user
    status_code, issue_response = create_issue(
        owner=owner_name,
        repo=repo_name,
        token=token,
        title=title,
        body=body,
        assignees=[user_name],
    )

    # Handle 410 - issues are disabled for this repository
    if status_code == 410:
        # Disable schedule trigger in database
        update_repository(
            owner_id=owner_id,
            repo_id=repo_id,
            trigger_on_schedule=False,
            updated_by=user_name,
        )

        # Delete AWS scheduler
        schedule_name = f"gitauto-repo-{owner_id}-{repo_id}"
        delete_scheduler(schedule_name)

        # Send email notification to user
        if user_id:
            user = get_user(user_id=user_id)
            email = user.get("email") if user else None
            if email:
                subject, text = get_issues_disabled_email_text(
                    user_name, owner_name, repo_name
                )
                send_email(to=email, subject=subject, text=text)

        msg = f"Issues are disabled for {owner_name}/{repo_name}. Disabled schedule trigger."
        logging.warning(msg)
        slack_notify(msg)
        return {"status": "skipped", "message": msg}

    if status_code == 200 and issue_response and "html_url" in issue_response:
        if target_item["id"] == 0:
            coverage_record: CoveragesInsert = {
                "full_path": target_item["full_path"],
                "owner_id": target_item["owner_id"],
                "repo_id": target_item["repo_id"],
                "branch_name": target_item["branch_name"],
                "created_by": target_item["created_by"],
                "updated_by": target_item["updated_by"],
                "level": target_item["level"],
                "file_size": target_item["file_size"],
                "statement_coverage": target_item["statement_coverage"],
                "function_coverage": target_item["function_coverage"],
                "branch_coverage": target_item["branch_coverage"],
                "line_coverage": target_item["line_coverage"],
                "path_coverage": target_item["path_coverage"],
                "package_name": target_item["package_name"],
                "language": target_item["language"],
                "github_issue_url": issue_response["html_url"],
                "is_excluded_from_testing": target_item["is_excluded_from_testing"],
                "uncovered_lines": target_item["uncovered_lines"],
                "uncovered_functions": target_item["uncovered_functions"],
                "uncovered_branches": target_item["uncovered_branches"],
            }
            insert_coverages(coverage_record)
        else:
            update_issue_url(
                owner_id=owner_id,
                repo_id=repo_id,
                file_path=target_path,
                github_issue_url=issue_response["html_url"],
            )

        msg = f"created issue for {target_path}"
        return {"status": "success", "message": msg}

    # Handle other errors
    msg = f"Failed to create issue for {target_path} (status: {status_code})"
    logging.error(msg)
    return {"status": "failed", "message": msg}
