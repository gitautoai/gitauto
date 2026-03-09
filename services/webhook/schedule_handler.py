# Standard imports
from datetime import datetime, timezone
from pathlib import Path

# Local imports
from config import PRODUCT_ID
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from schemas.supabase.types import Coverages, CoveragesInsert
from services.claude.evaluate_condition import evaluate_condition
from services.aws.delete_scheduler import delete_scheduler
from services.git.get_clone_url import get_clone_url
from services.github.branches.create_remote_branch import create_remote_branch
from services.github.branches.get_default_branch import get_default_branch
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.commits.get_latest_remote_commit_sha import (
    get_latest_remote_commit_sha,
)
from services.github.files.get_raw_content import get_raw_content
from services.github.labels.add_labels import add_labels
from services.github.repositories.is_repo_forked import is_repo_forked
from services.github.pulls.create_pull_request import create_pull_request
from services.github.pulls.get_open_pull_requests import get_open_pull_requests
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree import get_file_tree
from services.github.users.get_email_from_commits import get_email_from_commits
from services.github.users.get_user_public_email import get_user_public_info
from services.github.types.github_types import BaseArgs
from services.supabase.coverages.exclude_from_testing import exclude_from_testing
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.supabase.coverages.insert_coverages import insert_coverages
from services.supabase.coverages.update_issue_url import update_issue_url
from services.supabase.repositories.get_repository import get_repository
from services.supabase.schedule_pauses.is_schedule_paused import is_schedule_paused
from services.stripe.check_availability import check_availability
from utils.error.handle_exceptions import handle_exceptions
from utils.files.has_test_file_candidate import has_test_file_candidate
from utils.files.is_code_file import is_code_file
from utils.files.is_config_file import is_config_file
from utils.files.is_dependency_file import is_dependency_file
from utils.files.is_migration_file import is_migration_file
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file
from utils.files.should_skip_test import should_skip_test
from utils.generate_branch_name import generate_branch_name
from utils.pr_templates.schedule import get_pr_title, get_pr_body
from utils.logging.logging_config import logger, set_trigger
from utils.text.text_copy import git_command
from utils.prompts.should_test_file import SHOULD_TEST_FILE_PROMPT


@handle_exceptions(raise_on_error=True)
def schedule_handler(event: EventBridgeSchedulerEvent):
    set_trigger("schedule")
    # Extract details from the event payload
    owner_id = event["ownerId"]
    owner_name = event["ownerName"]
    repo_id = event["repoId"]
    repo_name = event["repoName"]
    user_name = event["userName"]
    installation_id = event["installationId"]

    # Get installation access token - simplified since we already have installation_id
    token = get_installation_access_token(installation_id=installation_id)
    if token is None:
        # Delete scheduler since installation is invalid
        schedule_name = f"gitauto-repo-{owner_id}-{repo_id}"
        delete_scheduler(schedule_name)
        msg = f"Installation {installation_id} no longer exists. Cleaned up scheduler."
        logger.info(msg)
        return {"status": "skipped", "message": msg}

    # Get repository settings - check if trigger_on_schedule is enabled
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_schedule"):
        msg = f"Skipping repo_id: {repo_id} - trigger_on_schedule is not enabled"
        logger.info(msg)
        return {"status": "skipped", "message": msg}

    # Check if schedule is paused for this repo
    if is_schedule_paused(owner_id=owner_id, repo_id=repo_id):
        msg = f"Skipping repo_id: {repo_id} - schedule is currently paused"
        logger.info(msg)
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
    target_branch = repo_settings.get("target_branch")
    if not target_branch:
        target_branch = get_default_branch(
            owner=owner_name, repo=repo_name, token=token
        ).default_branch
    tree_items = get_file_tree(
        owner=owner_name, repo=repo_name, ref=target_branch, token=token
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
                "branch_name": target_branch,
                "created_by": user_name,
                "updated_by": user_name,
                "level": "file",
                "file_size": file_size,
                "statement_coverage": 0,
                "function_coverage": 0,
                "branch_coverage": 0,
                "line_coverage": 0,
                "package_name": None,
                "language": None,
                "github_issue_url": None,
                "is_excluded_from_testing": False,
                "exclusion_reason": None,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            enriched_all_files.append(new_coverage)

    if not enriched_all_files:
        msg = "Schedule: No files found"
        logger.warning(msg)
        return {"status": "skipped", "message": msg}

    # Filter out files with 100% coverage in all three metrics
    files_needing_tests: list[Coverages] = []
    for item in enriched_all_files:
        stmt = item["statement_coverage"]
        func = item["function_coverage"]
        branch = item["branch_coverage"]
        logger.info(
            "Coverage for %s: stmt=%s, func=%s, branch=%s",
            item["full_path"],
            stmt,
            func,
            branch,
        )
        # None means "not measured" by the coverage tool (e.g. PHP doesn't report branch data).
        # If ALL three are None, the file was never measured at all — treat as uncovered.
        # E.g. finishp.php: stmt=None, func=None, branch=None → candidate
        # If only some are None, those metrics are N/A for the language — ignore them.
        # E.g. some PHP file: stmt=100, func=100, branch=None → skip (fully covered)
        metrics = (stmt, func, branch)
        all_none = all(v is None for v in metrics)
        all_complete = not all_none and all(v is None or v == 100.0 for v in metrics)
        if all_complete:
            logger.info("Skipping %s: all 3 metrics at 100%%", item["full_path"])
        elif item.get("is_excluded_from_testing"):
            continue
        else:
            logger.info("Adding to candidates: %s", item["full_path"])
            files_needing_tests.append(item)

    # Sort: prioritize untouched files (0% coverage) first, then by file_size, coverage, path
    # None (unmeasured) is treated as 0 for sorting purposes
    files_needing_tests.sort(
        key=lambda x: (
            1 if (x["statement_coverage"] or 0) > 0 else 0,
            x["file_size"] or 0,
            x["statement_coverage"] or 0,
            x["full_path"],
        )
    )

    # Get open PRs once before the loop
    open_prs = get_open_pull_requests(owner=owner_name, repo=repo_name, token=token)

    # Find the first suitable file from sorted list
    target_item = None
    for item in files_needing_tests:
        item_path = item["full_path"]
        logger.info(
            "Evaluating %s (stmt=%s, func=%s, branch=%s)",
            item_path,
            item["statement_coverage"],
            item["function_coverage"],
            item["branch_coverage"],
        )

        # Skip files excluded from testing first (avoid unnecessary work)
        if item.get("is_excluded_from_testing"):
            logger.info("Skipping %s: excluded from testing", item_path)
            continue

        # Skip non-code files
        if not is_code_file(item_path):
            logger.info("Skipping %s: not a code file", item_path)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, "not code file", user_name
            )
            continue

        # Skip third-party dependency files (e.g. vendor/, node_modules/)
        if is_dependency_file(item_path):
            logger.info("Skipping %s: third-party dependency", item_path)
            exclude_from_testing(
                owner_id,
                repo_id,
                item_path,
                target_branch,
                "dependency file",
                user_name,
            )
            continue

        # Skip test files
        if is_test_file(item_path):
            logger.info("Skipping %s: test file", item_path)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, "test file", user_name
            )
            continue

        # Skip config files
        if is_config_file(item_path):
            logger.info("Skipping %s: config file", item_path)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, "config file", user_name
            )
            continue

        # Skip types files
        if is_type_file(item_path):
            logger.info("Skipping %s: type file", item_path)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, "type file", user_name
            )
            continue

        # Skip migration files
        if is_migration_file(item_path):
            logger.info("Skipping %s: migration file", item_path)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, "migration file", user_name
            )
            continue

        # Skip files that only contain exports/re-exports or are empty
        content = get_raw_content(
            owner=owner_name,
            repo=repo_name,
            file_path=item_path,
            ref=target_branch,
            token=token,
        )
        # Skip empty files or files with only whitespace
        if not content or not content.strip():
            logger.info("Skipping %s: empty content", item_path)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, "empty file", user_name
            )
            continue

        # Skip files that should be skipped based on content
        if should_skip_test(item_path, content):
            logger.info("Skipping %s: should_skip_test=True", item_path)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, "only exports", user_name
            )
            continue

        # Skip files that have open PRs (temporary, don't exclude)
        matching_pr = next(
            (pr for pr in open_prs if item_path in pr.get("title", "")), None
        )
        if matching_pr:
            logger.info(
                "Skipping %s: has open PR #%s (%s)",
                item_path,
                matching_pr.get("number"),
                matching_pr.get("base", {}).get("ref"),
            )
            continue

        # Check if a test file already exists for this source file
        all_file_paths = [fp for fp, _ in all_files_with_sizes]
        has_tests = has_test_file_candidate(item_path, all_file_paths)

        # If tests already exist, the file is proven testable - skip AI evaluation
        if has_tests:
            logger.info(
                "Selected %s: existing tests found, skipping AI evaluation",
                item_path,
            )
            target_item = item
            break

        # Final check: Use Claude AI to determine if this file should be tested (expensive, so run last)
        eval_result = evaluate_condition(
            content=f"File path: {item_path}\n\nContent:\n{content}",
            system_prompt=SHOULD_TEST_FILE_PROMPT,
        )
        should_test, reason = eval_result.result, eval_result.reason
        if not should_test:
            logger.info("Skipping %s: %s", item_path, reason)
            exclude_from_testing(
                owner_id, repo_id, item_path, target_branch, reason, user_name
            )
            continue

        # Found the best suitable file
        logger.info("Selected %s: %s", item_path, reason)
        target_item = item
        break

    if target_item is None:
        checked_files = [f["full_path"] for f in files_needing_tests]
        msg = f"No suitable file found after checking {len(checked_files)} files: {checked_files}"
        logger.warning(msg)
        return {"status": "skipped", "message": msg}

    target_path = target_item["full_path"]

    # Check if a test file exists for this source file by matching filenames
    target_stem = Path(target_path).stem.lower()
    has_existing_tests = any(
        is_test_file(fp) and target_stem in fp.lower() for fp, _ in all_files_with_sizes
    )
    title = get_pr_title(target_path, has_existing_tests=has_existing_tests)
    body = get_pr_body(
        owner=owner_name,
        repo=repo_name,
        branch=target_branch,
        file_path=target_path,
        statement_coverage=target_item["statement_coverage"],
        function_coverage=target_item["function_coverage"],
        branch_coverage=target_item["branch_coverage"],
        line_coverage=target_item["line_coverage"],
        uncovered_lines=target_item["uncovered_lines"],
        uncovered_functions=target_item["uncovered_functions"],
        uncovered_branches=target_item["uncovered_branches"],
    )

    # Look up sender info from GitHub
    sender_info = get_user_public_info(username=user_name, token=token)
    sender_email = sender_info.email
    if not sender_email:
        sender_email = get_email_from_commits(
            owner=owner_name, repo=repo_name, username=user_name, token=token
        )

    # Create a PR
    new_branch = generate_branch_name(trigger="schedule")
    clone_url = get_clone_url(owner_name, repo_name, token)
    base_args: BaseArgs = {
        "owner_type": event["ownerType"],
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": clone_url,
        "is_fork": is_repo_forked(owner=owner_name, repo=repo_name, token=token),
        "base_branch": target_branch,
        "new_branch": new_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": event["userId"],
        "sender_name": user_name,
        "sender_email": sender_email,
        "sender_display_name": sender_info.display_name,
        "reviewers": [user_name],
        "github_urls": [],
        "other_urls": [],
        "clone_dir": "",  # Rebuilt by deconstruct_github_payload when labeled webhook fires
        "pr_number": 0,  # Set after create_pull_request below
        "pr_title": "",  # Set after create_pull_request below
        "pr_body": "",  # Set after create_pull_request below
        "pr_comments": [],
        "pr_creator": user_name,
    }
    latest_sha = get_latest_remote_commit_sha(clone_url=clone_url, base_args=base_args)
    create_remote_branch(sha=latest_sha, base_args=base_args)
    create_empty_commit(
        base_args=base_args, message="Initial empty commit to create PR [skip ci]"
    )
    pr_body = body + git_command(new_branch_name=new_branch)
    pr_url, pr_number = create_pull_request(
        body=pr_body, title=title, base_args=base_args
    )
    base_args["pr_number"] = pr_number
    base_args["pr_title"] = title
    base_args["pr_body"] = pr_body

    # Add gitauto label to trigger issues.labeled webhook, which runs the agent
    add_labels(
        owner=owner_name,
        repo=repo_name,
        pr_number=pr_number,
        token=token,
        labels=[PRODUCT_ID],
    )

    # Update coverage record with PR URL
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
            "package_name": target_item["package_name"],
            "language": target_item["language"],
            "github_issue_url": pr_url,
            "is_excluded_from_testing": target_item["is_excluded_from_testing"],
            "exclusion_reason": target_item["exclusion_reason"],
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
            github_issue_url=pr_url,
            updated_by=user_name,
        )

    msg = f"created PR for {target_path}: {pr_url}"
    return {"status": "success", "message": msg}
