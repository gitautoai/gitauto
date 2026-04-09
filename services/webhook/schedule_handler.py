# Standard imports
import hashlib
from datetime import datetime, timezone

# Local imports
from config import PRODUCT_ID
from constants.testing import (
    PERMANENT_EXCLUSION_REASONS,
    REASON_CONFIG,
    REASON_DEPENDENCY,
    REASON_EMPTY,
    REASON_MIGRATION,
    REASON_NOT_CODE,
    REASON_ONLY_EXPORTS,
    REASON_TEST,
    REASON_TYPE,
)
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from schemas.supabase.types import Coverages, CoveragesInsert
from services.claude.evaluate_condition import evaluate_condition
from services.claude.evaluate_quality_checks import evaluate_quality_checks
from services.aws.delete_scheduler import delete_scheduler
from services.git.create_empty_commit import create_empty_commit
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.create_remote_branch import create_remote_branch
from services.git.git_checkout import git_checkout
from services.git.git_fetch import git_fetch
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.get_default_branch import get_default_branch
from services.git.get_latest_remote_commit_sha import get_latest_remote_commit_sha
from services.git.get_file_tree import get_file_tree
from services.github.labels.add_labels import add_labels
from services.github.repositories.is_repo_forked import is_repo_forked
from services.github.pulls.create_pull_request import create_pull_request
from services.github.pulls.get_open_pull_requests import get_open_pull_requests
from services.github.token.get_installation_token import get_installation_access_token
from services.github.users.get_email_from_commits import get_email_from_commits
from services.github.users.get_user_public_email import get_user_public_info
from services.supabase.coverages.exclude_from_testing import exclude_from_testing
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.supabase.coverages.insert_coverages import insert_coverages
from services.supabase.coverages.update_issue_url import update_issue_url
from services.supabase.coverages.update_quality_checks import update_quality_checks
from services.supabase.repositories.get_repository import get_repository
from services.supabase.schedule_pauses.get_schedule_pause import get_schedule_pause
from services.stripe.check_availability import check_availability
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.find_test_files import find_test_files
from utils.files.read_local_file import read_local_file
from utils.files.is_code_file import is_code_file
from utils.files.is_config_file import is_config_file
from utils.files.is_dependency_file import is_dependency_file
from utils.files.is_migration_file import is_migration_file
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file
from utils.files.should_skip_test import should_skip_test
from utils.generate_branch_name import generate_branch_name
from utils.logging.logging_config import logger, set_trigger
from utils.pr_templates.schedule import get_pr_title, get_pr_body
from utils.prompts.should_test_file import SHOULD_TEST_FILE_PROMPT
from utils.quality_checks.get_checklist_hash import get_checklist_hash
from utils.quality_checks.needs_reevaluation import needs_quality_reevaluation
from utils.text.text_copy import git_command


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
    pause_info = get_schedule_pause(owner_id=owner_id, repo_id=repo_id)
    if pause_info:
        msg = f"Skipping repo_id: {repo_id} - schedule is paused from {pause_info.pause_start} to {pause_info.pause_end}"
        logger.info(msg)
        return {"status": "skipped", "message": msg}

    # Check availability
    availability_status = check_availability(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        sender_name=user_name,
    )

    if not availability_status["can_proceed"]:
        return {"status": "skipped", "message": availability_status["log_message"]}

    # Get repository files and coverage data
    clone_url = get_clone_url(owner_name, repo_name, token)
    target_branch = repo_settings.get("target_branch")
    if not target_branch:
        target_branch = get_default_branch(clone_url=clone_url)
        if not target_branch:
            msg = f"Repository {owner_name}/{repo_name} is empty"
            logger.info(msg)
            return {"status": "skipped", "message": msg}

    # Clone directly to /tmp
    clone_dir = get_clone_dir(owner_name, repo_name, pr_number=None)
    git_clone_to_tmp(clone_dir, clone_url, target_branch)
    tree_items = get_file_tree(clone_dir=clone_dir, ref=target_branch)

    # Extract necessary data
    all_files_with_sizes = [
        (item["path"], item.get("size", 0))
        for item in tree_items
        if item["type"] == "blob"  # Only files
    ]
    all_file_paths = [fp for fp, _ in all_files_with_sizes]

    # Build blob SHA lookup from tree (free, already fetched)
    blob_sha_map: dict[str, str] = {
        item["path"]: item["sha"] for item in tree_items if item["type"] == "blob"
    }

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
                "statement_coverage": None,
                "function_coverage": None,
                "branch_coverage": None,
                "line_coverage": None,
                "package_name": None,
                "language": None,
                "github_issue_url": None,
                "is_excluded_from_testing": False,
                "exclusion_reason": None,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
                "impl_blob_sha": None,
                "test_blob_sha": None,
                "checklist_hash": None,
                "quality_checks": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            enriched_all_files.append(new_coverage)

    if not enriched_all_files:
        msg = "Schedule: No files found"
        logger.warning(msg)
        return {"status": "skipped", "message": msg}

    # Separate files into coverage candidates (<100%) and quality-only candidates (100%)
    files_needing_coverage: list[Coverages] = []
    files_at_full_coverage: list[Coverages] = []
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
        # If ALL three are None, the file was never measured at all - treat as uncovered.
        # E.g. finishp.php: stmt=None, func=None, branch=None -> candidate
        # If only some are None, those metrics are N/A for the language - ignore them.
        # E.g. some PHP file: stmt=100, func=100, branch=None -> skip (fully covered)
        metrics = (stmt, func, branch)
        all_none = all(v is None for v in metrics)
        all_complete = not all_none and all(v is None or v == 100.0 for v in metrics)
        if all_complete:
            # Excluded files can still be quality-checked (they have existing tests)
            logger.info("Full coverage: %s", item["full_path"])
            files_at_full_coverage.append(item)
        elif item.get("is_excluded_from_testing"):
            # Path-based exclusions (config, type, migration, etc.) are permanent
            reason = item.get("exclusion_reason") or ""
            if reason in PERMANENT_EXCLUSION_REASONS:
                logger.info("Skipping %s: %s (permanent)", item["full_path"], reason)
                continue

            # LLM-evaluated exclusion — re-evaluate if impl changed
            current_sha = blob_sha_map.get(item["full_path"])
            stored_sha = item.get("impl_blob_sha")
            if current_sha and current_sha == stored_sha:
                logger.info(
                    "Skipping %s: LLM excluded, impl unchanged", item["full_path"]
                )
                continue

            logger.info(
                "Re-evaluating %s: LLM excluded but impl changed (%s -> %s)",
                item["full_path"],
                stored_sha,
                current_sha,
            )
            files_needing_coverage.append(item)
        else:
            logger.info("Adding to coverage candidates: %s", item["full_path"])
            files_needing_coverage.append(item)

    # Sort coverage candidates: untouched (0%) first, then by file_size, coverage, path
    # None (unmeasured) is treated as 0 for sorting purposes
    files_needing_coverage.sort(
        key=lambda x: (
            1 if (x["statement_coverage"] or 0) > 0 else 0,
            x["file_size"] or 0,
            x["statement_coverage"] or 0,
            x["full_path"],
        )
    )

    # Get open PRs once before the loop
    open_prs = get_open_pull_requests(owner=owner_name, repo=repo_name, token=token)

    # --- Phase 1: Find first file needing coverage improvement (PRIMARY) ---
    target_item = None
    target_test_file_paths: list[str] = []
    quality_only = False
    for item in files_needing_coverage:
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
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_NOT_CODE,
                updated_by=user_name,
                impl_blob_sha=None,
            )
            continue

        # Skip third-party dependency files (e.g. vendor/, node_modules/)
        if is_dependency_file(item_path):
            logger.info("Skipping %s: third-party dependency", item_path)
            exclude_from_testing(
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_DEPENDENCY,
                updated_by=user_name,
                impl_blob_sha=None,
            )
            continue

        # Skip test files
        if is_test_file(item_path):
            logger.info("Skipping %s: test file", item_path)
            exclude_from_testing(
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_TEST,
                updated_by=user_name,
                impl_blob_sha=None,
            )
            continue

        # Skip config files
        if is_config_file(item_path):
            logger.info("Skipping %s: config file", item_path)
            exclude_from_testing(
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_CONFIG,
                updated_by=user_name,
                impl_blob_sha=None,
            )
            continue

        # Skip types files
        if is_type_file(item_path):
            logger.info("Skipping %s: type file", item_path)
            exclude_from_testing(
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_TYPE,
                updated_by=user_name,
                impl_blob_sha=None,
            )
            continue

        # Skip migration files
        if is_migration_file(item_path):
            logger.info("Skipping %s: migration file", item_path)
            exclude_from_testing(
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_MIGRATION,
                updated_by=user_name,
                impl_blob_sha=None,
            )
            continue

        # Skip files that only contain exports/re-exports or are empty
        content = read_local_file(file_path=item_path, base_dir=clone_dir)
        # Skip empty files or files with only whitespace
        if not content or not content.strip():
            logger.info("Skipping %s: empty content", item_path)
            exclude_from_testing(
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_EMPTY,
                updated_by=user_name,
                impl_blob_sha=None,
            )
            continue

        # Skip files that should be skipped based on content
        if should_skip_test(item_path, content):
            logger.info("Skipping %s: should_skip_test=True", item_path)
            exclude_from_testing(
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=REASON_ONLY_EXPORTS,
                updated_by=user_name,
                impl_blob_sha=None,
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
        test_dir_prefixes = repo_settings.get("test_dir_prefixes")
        test_file_paths = find_test_files(item_path, all_file_paths, test_dir_prefixes)

        # If tests already exist, the file is proven testable - skip AI evaluation
        if test_file_paths:
            logger.info(
                "Selected %s: existing tests found, skipping AI evaluation",
                item_path,
            )
            target_item = item
            target_test_file_paths = test_file_paths
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
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=item_path,
                branch_name=target_branch,
                exclusion_reason=reason,
                updated_by=user_name,
                impl_blob_sha=blob_sha_map.get(item_path),
            )
            continue

        # Found the best suitable file (no existing tests, AI says testable)
        logger.info("Selected %s: %s", item_path, reason)
        target_item = item
        target_test_file_paths = []
        break

    # --- Phase 2: If no coverage target, find first file needing quality checks ---
    quality_results: dict[str, dict[str, dict[str, str]]] | None = None
    failed_categories: list[str] = []
    impl_sha = ""
    test_sha: str | None = None
    checklist_hash = ""

    if target_item is None:
        logger.info("No coverage target found, checking quality for 100%% files")
        checklist_hash = get_checklist_hash()

        for item in files_at_full_coverage:
            item_path = item["full_path"]

            # Skip non-code and test files (but NOT excluded files - quality checks still apply)
            if not is_code_file(item_path) or is_test_file(item_path):
                continue

            # Skip files with open PRs
            matching_pr = next(
                (pr for pr in open_prs if item_path in pr.get("title", "")), None
            )
            if matching_pr:
                logger.info(
                    "Skipping quality check for %s: has open PR #%s",
                    item_path,
                    matching_pr.get("number"),
                )
                continue

            # Check if quality re-evaluation is needed
            current_impl_sha = blob_sha_map.get(item_path, "")
            test_dir_prefixes = repo_settings.get("test_dir_prefixes")
            test_file_paths = find_test_files(
                item_path, all_file_paths, test_dir_prefixes
            )
            # Combined hash of all test file SHAs — any test change triggers re-eval
            test_shas = sorted(
                blob_sha_map[tp] for tp in test_file_paths if tp in blob_sha_map
            )
            current_test_sha = (
                hashlib.sha256("".join(test_shas).encode()).hexdigest()
                if test_shas
                else None
            )

            if not needs_quality_reevaluation(
                coverage=item,
                current_impl_sha=current_impl_sha,
                current_test_sha=current_test_sha,
                current_checklist_hash=checklist_hash,
            ):
                continue

            # Fetch source and test content
            source_content = read_local_file(file_path=item_path, base_dir=clone_dir)
            if not source_content or not source_content.strip():
                logger.info("Skipping quality check for %s: empty content", item_path)
                continue

            # Fetch all test file contents
            test_files: list[tuple[str, str]] = []
            for tp in test_file_paths:
                content = read_local_file(file_path=tp, base_dir=clone_dir)
                if content and content.strip():
                    test_files.append((tp, content))

            # Run quality checks via Claude
            logger.info("Evaluating quality checks for %s", item_path)
            quality_results = evaluate_quality_checks(
                source_content=source_content,
                source_path=item_path,
                test_files=test_files,
            )
            if quality_results is None:
                logger.warning(
                    "Quality check evaluation failed for %s, skipping", item_path
                )
                continue

            # Collect categories with at least one failing check
            for category, checks in quality_results.items():
                for check_data in checks.values():
                    if check_data.get("status") == "fail":
                        logger.info(
                            "Quality check failed in %s for %s", category, item_path
                        )
                        failed_categories.append(category)
                        # One failure is enough to flag the category
                        break

            if not failed_categories:
                # All passed - update DB, continue to next file
                logger.info("All quality checks passed for %s", item_path)
                update_quality_checks(
                    owner_id=owner_id,
                    repo_id=repo_id,
                    file_path=item_path,
                    impl_blob_sha=current_impl_sha,
                    test_blob_sha=current_test_sha,
                    checklist_hash=checklist_hash,
                    quality_checks=quality_results,
                    updated_by=user_name,
                )
                continue

            # Quality failures found - this file becomes the target
            logger.info("Quality failures for %s: %s", item_path, failed_categories)
            target_item = item
            target_test_file_paths = test_file_paths
            impl_sha = current_impl_sha
            test_sha = current_test_sha
            quality_only = True
            break

    if target_item is None:
        logger.info("No target file found from either coverage or quality loops")
        checked_files = [f["full_path"] for f in files_needing_coverage]
        quality_files = [f["full_path"] for f in files_at_full_coverage]
        msg = (
            f"No suitable file found after checking"
            f" {len(checked_files)} coverage files: {checked_files},"
            f" {len(quality_files)} quality files: {quality_files}"
        )
        logger.warning(msg)
        return {"status": "skipped", "message": msg}

    logger.info(
        "Target file: %s (quality_only=%s)", target_item["full_path"], quality_only
    )

    # --- Build PR title and body ---
    target_path = target_item["full_path"]
    has_existing_tests = bool(target_test_file_paths)

    title = get_pr_title(
        target_path,
        has_existing_tests=has_existing_tests,
        quality_only=quality_only,
        failed_categories=failed_categories,
    )

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
        quality_checks=quality_results,
    )

    # --- Create PR (shared for both coverage and quality) ---
    sender_info = get_user_public_info(username=user_name, token=token)
    sender_email = sender_info.email
    if not sender_email:
        sender_email = get_email_from_commits(
            owner=owner_name, repo=repo_name, username=user_name, token=token
        )

    # Create a PR
    new_branch = generate_branch_name(trigger="schedule")
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
        "clone_dir": clone_dir,
        "pr_number": 0,  # Set after create_pull_request below
        "pr_title": "",  # Set after create_pull_request below
        "pr_body": "",  # Set after create_pull_request below
        "pr_comments": [],
        "pr_creator": user_name,
    }
    latest_sha = get_latest_remote_commit_sha(clone_url=clone_url, base_args=base_args)
    create_remote_branch(sha=latest_sha, base_args=base_args)

    # Fetch and checkout the new branch so HEAD matches the remote tip
    git_fetch(clone_dir, clone_url, new_branch)
    git_checkout(clone_dir, new_branch)
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

    # --- Update DB records ---
    if quality_only and quality_results:
        # Update quality check results
        update_quality_checks(
            owner_id=owner_id,
            repo_id=repo_id,
            file_path=target_path,
            impl_blob_sha=impl_sha,
            test_blob_sha=test_sha,
            checklist_hash=checklist_hash,
            quality_checks=quality_results,
            updated_by=user_name,
        )
        # Also update issue URL
        update_issue_url(
            owner_id=owner_id,
            repo_id=repo_id,
            file_path=target_path,
            github_issue_url=pr_url,
            updated_by=user_name,
        )
    elif target_item["id"] == 0:
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
            # SHAs/hash only set when quality is actually evaluated (Phase 2)
            "impl_blob_sha": None,
            "test_blob_sha": None,
            "checklist_hash": None,
            "quality_checks": None,
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
    logger.info(msg)
    return {"status": "success", "message": msg}
