# Standard imports
import logging
import json

# Local imports
from schemas.supabase.types import RepoCoverageInsert
from services.coverages.parse_lcov_coverage import parse_lcov_coverage
from services.coverages.coverage_types import CoverageReport
from services.github.artifacts.download_artifact import download_artifact
from services.github.artifacts.get_workflow_artifacts import get_workflow_artifacts
from services.circleci.download_circleci_artifact import download_circleci_artifact
from services.circleci.get_job_artifacts import get_circleci_job_artifacts
from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs
from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token
from services.github.token.get_installation_token import get_installation_access_token
from services.github.check_suites.get_circleci_workflow_id import (
    get_circleci_workflow_ids_from_check_suite,
)
from services.github.trees.get_file_tree import get_file_tree
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.coverages.upsert_coverages import upsert_coverages
from services.supabase.repo_coverage.upsert_repo_coverage import upsert_repo_coverage

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file
from utils.languages.detect_language_from_coverage import detect_language_from_coverage


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_coverage_report(
    owner_id: int,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    installation_id: int,
    run_id: int,
    head_branch: str,
    user_name: str,
    source: str = "github",
):
    github_token = get_installation_access_token(installation_id=installation_id)
    circle_token = None
    if source == "github":
        artifacts = get_workflow_artifacts(owner_name, repo_name, run_id, github_token)
    elif source == "circleci":
        token_record = get_circleci_token(owner_id=owner_id)
        if not token_record:
            logging.warning("No CircleCI token found for owner %d", owner_id)
            return None
        circle_token = token_record["token"]
        circleci_workflow_ids = get_circleci_workflow_ids_from_check_suite(
            owner_name, repo_name, run_id, github_token
        )
        if not circleci_workflow_ids:
            logging.warning(
                "Failed to get CircleCI workflow IDs from check suite %d", run_id
            )
            return None

        project_slug = f"gh/{owner_name}/{repo_name}"
        artifacts = []

        # Try each workflow ID until we find coverage artifacts
        for workflow_id in circleci_workflow_ids:
            logging.info("Checking CircleCI workflow ID: %s", workflow_id)
            jobs = get_circleci_workflow_jobs(
                workflow_id=workflow_id, circle_token=circle_token
            )
            for job in jobs:
                logging.info(
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

    coverage_data: list[CoverageReport] = []
    logging.info(f"DEBUG: Processing {len(artifacts)} artifacts for {owner_name}/{repo_name}")
    
    for artifact in artifacts:
        if source == "github":
            artifact_name = artifact.get("name", "")
        else:
            artifact_name = artifact.get("path", "")

        logging.info(f"DEBUG: Processing artifact: {artifact_name}")

        # Check for coverage artifacts - lcov files, coverage reports, or default artifact
        if not artifact_name.endswith("lcov.info"):
            logging.info(f"DEBUG: Skipping non-lcov artifact: {artifact_name}")
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
            logging.info("Downloading CircleCI artifact from %s", artifact_name)
            lcov_content = download_circleci_artifact(
                artifact_url=artifact["url"], token=circle_token
            )

        if not lcov_content:
            logging.warning(f"DEBUG: No content downloaded from artifact: {artifact_name}")
            continue

        logging.info(f"DEBUG: Downloaded lcov content, size: {len(lcov_content)} chars")
        parsed_coverage = parse_lcov_coverage(lcov_content)
        
        if parsed_coverage:
            logging.info(f"DEBUG: Parsed {len(parsed_coverage)} coverage items")
            levels = [item.get('level') for item in parsed_coverage]
            logging.info(f"DEBUG: Coverage levels found: {levels}")
            
            report_language = detect_language_from_coverage(parsed_coverage)
            logging.info(f"DEBUG: Detected language: {report_language}")

            for item in parsed_coverage:
                item["language"] = report_language
                # LCOV doesn't provide path coverage, use branch coverage as closest approximation
                item["path_coverage"] = item["branch_coverage"]

            coverage_data.extend(parsed_coverage)
        else:
            logging.warning(f"DEBUG: No parsed coverage from artifact: {artifact_name}")

    logging.info(f"DEBUG: Total coverage_data items: {len(coverage_data)}")

    if not coverage_data:
        return None

    # Add uncovered source files
    tree_items = get_file_tree(owner_name, repo_name, head_branch, github_token)

    all_files = [item["path"] for item in tree_items if item["type"] == "blob"]
    source_files = [
        f
        for f in all_files
        if is_code_file(f) and not is_test_file(f) and not is_type_file(f)
    ]

    covered_files = {
        report["full_path"] for report in coverage_data if report["level"] == "file"
    }

    for source_file in source_files:
        if source_file not in covered_files:
            coverage_data.append(
                {
                    "package_name": None,
                    "language": "unknown",
                    "level": "file",
                    "full_path": source_file,
                    "statement_coverage": 0.0,
                    "function_coverage": 0.0,
                    "branch_coverage": 0.0,
                    "line_coverage": 0.0,
                    "path_coverage": 0.0,
                    "uncovered_lines": "",
                    "uncovered_functions": "",
                    "uncovered_branches": "",
                }
            )

    # Remove duplicates
    seen: dict[tuple[int, str], CoverageReport] = {}
    for coverage in coverage_data:
        key = (repo_id, coverage["full_path"])
        if key in seen:
            msg = f"Duplicate coverage for `{owner_name}/{repo_name}`, full_path=`{coverage['full_path']}`"
            logging.warning(msg)
        seen[key] = coverage

    # Get current file paths
    current_paths = [coverage["full_path"] for coverage in seen.values()]

    # Get existing records
    existing_records = get_coverages(repo_id=repo_id, filenames=current_paths)

    # Prepare data for upsert
    upsert_data = []
    for coverage in seen.values():
        try:
            existing_record = existing_records.get(coverage["full_path"]) or {}
            item = {
                **existing_record,
                "owner_id": owner_id,
                "repo_id": repo_id,
                "branch_name": head_branch,
                "language": coverage.get("language", "unknown"),
                "path_coverage": 0,
                "updated_by": user_name,
                **coverage,
            }

            if not existing_record:
                item["created_by"] = user_name
                item["is_excluded_from_testing"] = False

            # Set None for 100% coverage fields
            if item.get("line_coverage") == 100:
                item["uncovered_lines"] = None
            if item.get("function_coverage") == 100:
                item["uncovered_functions"] = None
            if item.get("branch_coverage") == 100:
                item["uncovered_branches"] = None

            # Remove fields that cause upsert conflicts
            for field in ["id", "created_at", "updated_at"]:
                item.pop(field, None)

            json.dumps(item)
            upsert_data.append(item)
        except (TypeError, ValueError, OverflowError) as e:
            msg = f"Skipping non-serializable item: {str(e)}\nItem data: {coverage}"
            logging.warning(msg)
            continue

    if not upsert_data:
        logging.warning("No valid items to upsert")
        return None

    # Extract repository-level coverage for historical tracking
    repo_coverage = next((c for c in coverage_data if c["level"] == "repository"), None)
    logging.info(f"DEBUG: Looking for repository-level coverage in {len(coverage_data)} items")
    logging.info(f"DEBUG: Found repo_coverage: {repo_coverage}")

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
            "created_by": user_name,
        }
        
        logging.info(f"DEBUG: Calling upsert_repo_coverage with data: {repo_coverage_data}")
        result = upsert_repo_coverage(repo_coverage_data)
        logging.info(f"DEBUG: upsert_repo_coverage result: {result}")
    else:
        logging.warning(f"DEBUG: No repository-level coverage found. Coverage data levels: {[c.get('level') for c in coverage_data]}")

    # Upsert file coverages
    return upsert_coverages(upsert_data)
