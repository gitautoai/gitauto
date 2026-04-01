# Standard imports
from collections import Counter
import json

# Local imports
from schemas.supabase.types import RepoCoverageInsert
from services.coverages.parse_lcov_coverage import parse_lcov_coverage
from services.coverages.coverage_types import CoverageReport
from services.efs.get_efs_dir import get_efs_dir
from services.git.get_file_tree import get_file_tree
from services.github.artifacts.download_artifact import download_artifact
from services.github.artifacts.get_workflow_artifacts import get_workflow_artifacts
from services.circleci.download_circleci_artifact import download_circleci_artifact
from services.circleci.get_job_artifacts import get_circleci_job_artifacts
from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs
from services.git.check_branch_exists import check_branch_exists
from services.git.get_branch_head import get_branch_head
from services.git.get_clone_url import get_clone_url
from services.git.get_default_branch import get_default_branch
from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token
from services.supabase.repositories.get_repository import get_repository
from services.supabase.repositories.update_repository import update_repository
from services.github.token.get_installation_token import get_installation_access_token
from services.github.check_suites.get_circleci_workflow_id import (
    get_circleci_workflow_ids_from_check_suite,
)
from services.supabase.coverages.delete_stale_coverages import delete_stale_coverages
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.coverages.upsert_coverages import upsert_coverages
from services.supabase.repo_coverage.upsert_repo_coverage import upsert_repo_coverage

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.languages.detect_language_from_coverage import detect_language_from_coverage
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_coverage_report(
    owner_id: int,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    installation_id: int,
    run_id: int,
    head_branch: str | None,
    head_sha: str,
    user_name: str,
    source: str = "github",
):
    # Default to "detached" for builds without branch context (tag builds, API triggers, etc.)
    if head_branch is None:
        head_branch = "detached"
        logger.info(
            "No branch context for coverage report (run_id: %s, source: %s). Using 'detached'.",
            run_id,
            source,
        )

    github_token = get_installation_access_token(installation_id=installation_id)
    if not github_token:
        raise ValueError(
            f"No token for installation {installation_id} ({owner_name}/{repo_name})"
        )

    clone_url = get_clone_url(owner_name, repo_name, github_token)

    # Only process coverage for target branch
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    target_branch = repo_settings.get("target_branch") if repo_settings else ""
    if target_branch and not check_branch_exists(
        clone_url=clone_url, branch_name=target_branch
    ):
        logger.warning(
            "target_branch '%s' no longer exists for %s/%s, clearing and falling back to default branch",
            target_branch,
            owner_name,
            repo_name,
        )
        update_repository(owner_id=owner_id, repo_id=repo_id, target_branch="")
        target_branch = ""
    if not target_branch:
        target_branch = get_default_branch(clone_url=clone_url)
        if not target_branch:
            logger.warning("Repository %s/%s is empty", owner_name, repo_name)
            return None

    # Check if head_sha is the HEAD of target branch. This handles: PR merge, direct push, manual trigger on target branch
    target_head = get_branch_head(clone_url=clone_url, branch=target_branch)
    if head_sha == target_head:
        logger.info(
            "Commit %s is HEAD of %s, saving coverage (head_branch was %s)",
            head_sha[:7],
            target_branch,
            head_branch,
        )
        head_branch = target_branch
    elif head_branch != target_branch:
        logger.info(
            "Skipping saving coverage to Supabase: head_branch=%s != target_branch=%s, head_sha=%s != target_head=%s",
            head_branch,
            target_branch,
            head_sha[:7],
            target_head[:7] if target_head else None,
        )
        return None

    circle_token = None
    if source == "github":
        artifacts = get_workflow_artifacts(owner_name, repo_name, run_id, github_token)
    elif source == "circleci":
        circle_token = get_circleci_token(owner_id=owner_id)
        if not circle_token:
            logger.warning("No CircleCI token found for owner %d", owner_id)
            return None
        circleci_workflow_ids = get_circleci_workflow_ids_from_check_suite(
            owner_name, repo_name, run_id, github_token
        )
        if not circleci_workflow_ids:
            logger.warning(
                "Failed to get CircleCI workflow IDs from check suite %d", run_id
            )
            return None

        project_slug = f"gh/{owner_name}/{repo_name}"
        artifacts = []

        # Try each workflow ID until we find coverage artifacts
        for workflow_id in circleci_workflow_ids:
            logger.info("Checking CircleCI workflow ID: %s", workflow_id)
            jobs = get_circleci_workflow_jobs(
                workflow_id=workflow_id, circle_token=circle_token
            )
            for job in jobs:
                logger.info(
                    "Found CircleCI job: %s (status: %s)", job["name"], job["status"]
                )
                if job["status"] != "success":
                    continue

                job_artifacts = get_circleci_job_artifacts(
                    project_slug=project_slug,
                    job_number=str(job["job_number"]),
                    circle_token=circle_token,
                )
                artifacts.extend(job_artifacts)
    else:
        return None

    # Fetch file tree early to normalize absolute paths in lcov files
    efs_dir = get_efs_dir(owner_name, repo_name)
    tree_items = get_file_tree(clone_dir=efs_dir, ref=head_branch)
    repo_files = {item["path"] for item in tree_items if item["type"] == "blob"}

    coverage_data: list[CoverageReport] = []
    logger.info(
        "Processing %d artifacts for %s/%s", len(artifacts), owner_name, repo_name
    )

    for artifact in artifacts:
        # GitHub API returns "name": https://docs.github.com/en/rest/actions/artifacts
        # CircleCI API returns "path" (no name field): https://circleci.com/docs/api/v2/#operation/getJobArtifacts
        if source == "github":
            artifact_name = artifact.get("name", "")
        else:
            artifact_name = artifact.get("path", "")

        logger.info("Processing artifact: %s", artifact_name)

        # Check for coverage artifacts by artifact name (GitHub) or path (CircleCI)
        # GitHub Actions artifact names: "coverage-report", "php-coverage", "js-coverage"
        # CircleCI artifact paths: "lcov.info", "php/lcov.info", "js/lcov.info"
        artifact_name_lower = artifact_name.lower()
        if not (
            "lcov.info" in artifact_name_lower or "coverage" in artifact_name_lower
        ):
            logger.info("Skipping non-coverage artifact: %s", artifact_name)
            continue

        if source == "github":
            lcov_content = download_artifact(
                owner=owner_name,
                repo=repo_name,
                artifact_id=artifact["id"],
                token=github_token,
            )
        else:
            if not circle_token:
                continue
            logger.info("Downloading CircleCI artifact from %s", artifact_name)
            lcov_content = download_circleci_artifact(
                artifact_url=artifact["url"], token=circle_token
            )

        if not lcov_content:
            logger.warning("No content downloaded from artifact: %s", artifact_name)
            continue

        logger.info("Downloaded lcov content, size: %d chars", len(lcov_content))
        parsed_coverage = parse_lcov_coverage(lcov_content, repo_files)

        if parsed_coverage:
            logger.info("Parsed %d coverage items", len(parsed_coverage))
            level_counts = Counter(item.get("level") for item in parsed_coverage)
            logger.info("Coverage levels: %s", dict(level_counts))

            report_language = detect_language_from_coverage(parsed_coverage)
            logger.info("Detected language: %s", report_language)

            for item in parsed_coverage:
                item["language"] = report_language

            coverage_data.extend(parsed_coverage)
        else:
            logger.warning("No parsed coverage from artifact: %s", artifact_name)

    logger.info("Total coverage_data items: %d", len(coverage_data))

    if not coverage_data:
        return None

    # Remove duplicates
    seen: dict[tuple[int, str], CoverageReport] = {}
    for coverage in coverage_data:
        key = (repo_id, coverage["full_path"])
        if key in seen:
            msg = f"Duplicate coverage for `{owner_name}/{repo_name}`, full_path=`{coverage['full_path']}`"
            logger.warning(msg)
        seen[key] = coverage

    # Get current file paths
    current_paths = [coverage["full_path"] for coverage in seen.values()]

    # Get existing records
    existing_records = get_coverages(
        owner_id=owner_id, repo_id=repo_id, filenames=current_paths
    )

    # Prepare data for upsert (file-level only, not directory or repository aggregates)
    upsert_data = []
    for coverage in seen.values():
        if coverage.get("level") != "file":
            continue
        try:
            existing_record = existing_records.get(coverage["full_path"]) or {}
            item = {
                **existing_record,
                "owner_id": owner_id,
                "repo_id": repo_id,
                "branch_name": head_branch,
                "language": coverage.get("language", "unknown"),
                "updated_by": user_name,
                **coverage,
            }

            if not existing_record:
                item["created_by"] = user_name
                item["is_excluded_from_testing"] = False
                # SHAs not available here: CI coverage reports don't include git tree data
                item["impl_blob_sha"] = None
                item["test_blob_sha"] = None
                item["checklist_hash"] = None
                item["quality_checks"] = None

            # Set None for 100% coverage fields
            if item.get("line_coverage") == 100:
                item["uncovered_lines"] = None
            if item.get("function_coverage") == 100:
                item["uncovered_functions"] = None
            if item.get("branch_coverage") == 100:
                item["uncovered_branches"] = None

            # Remove fields that cause upsert conflicts or don't exist in coverages table
            for field in [
                "id",
                "created_at",
                "updated_at",
                "lines_covered",
                "lines_total",
                "functions_covered",
                "functions_total",
                "branches_covered",
                "branches_total",
            ]:
                item.pop(field, None)

            json.dumps(item)
            upsert_data.append(item)
        except (TypeError, ValueError, OverflowError) as e:
            msg = f"Skipping non-serializable item: {str(e)}\nItem data: {coverage}"
            logger.warning(msg)
            continue

    if not upsert_data:
        logger.warning("No valid items to upsert")
        return None

    # Extract repository-level coverage for historical tracking
    repo_coverage = next((c for c in coverage_data if c["level"] == "repository"), None)
    logger.info("Looking for repository-level coverage in %d items", len(coverage_data))

    if repo_coverage:
        repo_coverage_data: RepoCoverageInsert = {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "repo_id": repo_id,
            "repo_name": repo_name,
            "branch_name": head_branch,
            "language": coverage_data[0].get("language", "unknown"),
            "line_coverage": repo_coverage["line_coverage"],
            "statement_coverage": repo_coverage["statement_coverage"],
            "function_coverage": repo_coverage["function_coverage"],
            "branch_coverage": repo_coverage["branch_coverage"],
            "lines_covered": repo_coverage["lines_covered"],
            "lines_total": repo_coverage["lines_total"],
            "functions_covered": repo_coverage["functions_covered"],
            "functions_total": repo_coverage["functions_total"],
            "branches_covered": repo_coverage["branches_covered"],
            "branches_total": repo_coverage["branches_total"],
            "created_by": user_name,
        }

        upsert_repo_coverage(repo_coverage_data)

    # Log files being upserted with their coverage values
    for item in upsert_data:
        logger.info(
            "Upserting coverage for %s (stmt=%s, func=%s, branch=%s)",
            item.get("full_path"),
            item.get("statement_coverage"),
            item.get("function_coverage"),
            item.get("branch_coverage"),
        )

    # Upsert file coverages
    upsert_result = upsert_coverages(upsert_data)
    logger.info("Upserted %d coverage records", len(upsert_data))

    # Delete coverage records for files that no longer exist in the repo
    delete_stale_coverages(
        owner_id=owner_id,
        repo_id=repo_id,
        current_files=repo_files,
    )

    return upsert_result
