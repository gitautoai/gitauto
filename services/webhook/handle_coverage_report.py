# Standard imports
import logging
from typing import TypedDict, Literal
import json

# Local imports
from services.coverages.parse_lcov_coverage import parse_lcov_coverage
from services.github.artifacts.download_artifact import download_artifact
from services.github.artifacts.get_workflow_artifacts import get_workflow_artifacts
from services.github.repositories.get_repository_languages import (
    get_repository_languages,
)
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree import get_file_tree
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.coverages.upsert_coverages import upsert_coverages
from services.supabase.repo_coverage.upsert_repo_coverage import upsert_repo_coverage

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file


class CoverageItem(TypedDict):
    package_name: str
    level: Literal["repository", "directory", "file"]
    full_path: str
    line_coverage: float
    statement_coverage: float
    function_coverage: float
    branch_coverage: float
    path_coverage: float
    uncovered_lines: str
    uncovered_functions: str
    uncovered_branches: str


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_coverage_report(
    owner_id: int,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    installation_id: int,
    run_id: int,
    head_branch: str,
    user_name: str,
):
    token = get_installation_access_token(installation_id=installation_id)

    languages = get_repository_languages(owner=owner_name, repo=repo_name, token=token)
    primary_language = "unknown"
    if languages:
        primary_language = max(languages.items(), key=lambda x: x[1])[0].lower()

    artifacts = get_workflow_artifacts(owner_name, repo_name, run_id, token)

    coverage_data: list[CoverageItem] = []
    for artifact in artifacts:
        if "coverage" not in artifact["name"].lower():
            continue

        lcov_content = download_artifact(
            owner=owner_name, repo=repo_name, artifact_id=artifact["id"], token=token
        )

        if not lcov_content:
            continue

        parsed_coverage = parse_lcov_coverage(lcov_content)
        if parsed_coverage:
            coverage_data.extend(parsed_coverage)

    if not coverage_data:
        return None

    # Add uncovered source files
    tree_items = get_file_tree(owner_name, repo_name, head_branch, token)

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
                    "level": "file",
                    "full_path": source_file,
                    "statement_coverage": 0.0,
                    "function_coverage": 0.0,
                    "branch_coverage": 0.0,
                    "line_coverage": 0.0,
                    "uncovered_lines": "",
                    "uncovered_functions": "",
                    "uncovered_branches": "",
                }
            )

    # Remove duplicates
    seen: dict[tuple[int, str], CoverageItem] = {}
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
                "primary_language": primary_language,
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

    if repo_coverage:
        repo_coverage_data = {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "repo_id": repo_id,
            "repo_name": repo_name,
            "branch_name": head_branch,
            "primary_language": primary_language,
            "line_coverage": repo_coverage["line_coverage"],
            "statement_coverage": repo_coverage["statement_coverage"],
            "function_coverage": repo_coverage["function_coverage"],
            "branch_coverage": repo_coverage["branch_coverage"],
            "created_by": user_name,
        }

        upsert_repo_coverage(repo_coverage_data)

    # Upsert file coverages
    return upsert_coverages(upsert_data)
