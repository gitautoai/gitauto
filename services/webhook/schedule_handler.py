# Standard imports
import logging
from typing import cast

# Local imports (Types)
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from schemas.supabase.types import Coverages

# Local imports (AWS)
from services.aws.delete_scheduler import delete_scheduler

# Local imports (GitHub)
from services.github.branches.get_default_branch import get_default_branch
from services.github.files.get_raw_content import get_raw_content
from services.github.issues.create_issue import create_issue
from services.github.issues.is_issue_open import is_issue_open
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree import get_file_tree

# Local imports (Supabase)
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.supabase.coverages.insert_coverages import insert_coverages
from services.supabase.coverages.update_issue_url import update_issue_url
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.is_request_limit_reached import is_request_limit_reached

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_migration_file import is_migration_file
from utils.files.should_skip_test import should_skip_test
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file
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
        raise ValueError(f"Token is None for installation_id: {installation_id}")

    # Get repository settings - check if trigger_on_schedule is enabled
    repo_settings = get_repository(repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_schedule"):
        msg = f"Skipping repo_id: {repo_id} - trigger_on_schedule is not enabled"
        logging.info(msg)
        return {"status": "skipped", "message": msg}

    # Check the remaining available usage count
    limit_result = is_request_limit_reached(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repo_name=repo_name,
        issue_number=None,
    )
    is_limit_reached = limit_result["is_limit_reached"]
    # _requests_left = limit_result["requests_left"]
    # _request_limit = limit_result["request_limit"]
    # _end_date = limit_result["end_date"]
    # is_credit_user = limit_result["is_credit_user"]
    if is_limit_reached:
        msg = f"Request limit reached for {owner_name}/{repo_name}"
        return {"status": "skipped", "message": msg}

    # Get repository files and coverage data
    default_branch, _ = get_default_branch(
        owner=owner_name, repo=repo_name, token=token
    )
    base_args = {
        "owner": owner_name,
        "repo": repo_name,
        "token": token,
        "base_branch": default_branch,
    }
    tree_items = get_file_tree(
        owner=owner_name, repo=repo_name, ref=default_branch, token=token
    )

    # Extract necessary data
    all_files_with_sizes = [
        (item["path"], item.get("size", 0))
        for item in tree_items
        if item["type"] == "blob"  # Only files
    ]

    all_coverages = get_all_coverages(repo_id=repo_id)

    # all_files LEFT JOIN all_coverages
    enriched_all_files: list[Coverages] = []
    for file_path, file_size in all_files_with_sizes:
        coverages = next(
            (c for c in all_coverages if c["full_path"] == file_path), None
        )
        if coverages:
            enriched_all_files.append(
                {
                    **coverages,
                    "file_size": file_size,  # Use the latest file size
                }
            )
        else:
            enriched_all_files.append(
                {
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
                    "primary_language": None,
                    "github_issue_url": None,
                    "is_excluded_from_testing": False,
                    "uncovered_lines": None,
                    "uncovered_functions": None,
                    "uncovered_branches": None,
                    "created_at": None,
                    "updated_at": None,
                }
            )

    if not enriched_all_files:
        msg = f"No files found for {owner_name}/{repo_name}"
        logging.info(msg)
        return {"status": "skipped", "message": msg}

    # Filter out files with 100% coverage in all three metrics, then sort by file_size (asc), full_path (asc)
    files_needing_tests = [
        item
        for item in enriched_all_files
        if not (
            cast(float, item["statement_coverage"]) == 100.0
            and cast(float, item["function_coverage"]) == 100.0
            and cast(float, item["branch_coverage"]) == 100.0
        )
    ]

    files_needing_tests.sort(
        key=lambda x: (
            cast(int, x["file_size"]),
            cast(float, x["statement_coverage"]),
            cast(str, x["full_path"]),
        )
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

        # Skip files that have open GitHub issues
        github_issue_url = cast(str | None, item.get("github_issue_url"))
        if github_issue_url and is_issue_open(issue_url=github_issue_url, token=token):
            continue

        # Found the best suitable file
        target_item = item
        break

    if target_item is None:
        msg = f"No suitable file found for {owner_name}/{repo_name}"
        logging.info(msg)
        return {"status": "skipped", "message": msg}

    target_path = cast(str, target_item["full_path"])
    statement_coverage = cast(float, target_item["statement_coverage"])

    # Create issue title and body
    title = get_issue_title(target_path)
    body = get_issue_body(
        owner=owner_name,
        repo=repo_name,
        branch=default_branch,
        file_path=target_path,
        statement_coverage=statement_coverage,
    )

    # Create the issue with gitauto label and assign to the user
    issue_response = create_issue(
        title=title, body=body, assignees=[user_name], base_args=base_args
    )

    if issue_response and "html_url" in issue_response:
        if target_item["id"] == 0:
            coverage_record = {**target_item}
            coverage_record.pop("id")
            coverage_record.pop("created_at")
            coverage_record.pop("updated_at")
            coverage_record["github_issue_url"] = issue_response["html_url"]
            insert_coverages(coverage_record)
        else:
            update_issue_url(
                repo_id=repo_id,
                file_path=target_path,
                github_issue_url=issue_response["html_url"],
            )

    msg = f"created issue for {target_path}"
    return {"status": "success", "message": msg}
