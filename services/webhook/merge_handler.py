from config import PRODUCT_ID
from services.github.github_types import GitHubPullRequestClosedPayload, BaseArgs
from services.github.pull_requests.get_pull_request_files import get_pull_request_files
from services.github.token.get_installation_token import get_installation_access_token
from services.github.issues.create_issue import create_issue
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.repositories.get_repository import get_repository_settings
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_excluded_from_testing import is_excluded_from_testing
from utils.files.is_test_file import is_test_file
from utils.issue_templates.merge import (
    get_issue_title_for_pr_merged,
    get_issue_body_for_pr_merged,
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_pr_merged(payload: GitHubPullRequestClosedPayload):
    """
    Handle PR merged event by creating an issue for missing unit tests
    when trigger_on_merged is set to True in repository settings.

    Targets all code files changed in the PR, regardless of whether coverage data exists.
    """

    # Get repository info
    repository = payload["repository"]
    owner = repository["owner"]["login"]
    repo = repository["name"]
    repo_id = repository["id"]
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)

    # Get repository settings
    repo_settings = get_repository_settings(repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_merged", False):
        return

    # Get PR number and details
    pr_number = payload["number"]
    pull_request = payload["pull_request"]
    pull_url = pull_request["url"]

    # Get files changed in the PR
    pull_files_url = f"{pull_url}/files"
    changed_filenames = get_pull_request_files(url=pull_files_url, token=token)

    # Filter for code files that might need tests
    coverage_data = get_coverages(repo_id=repo_id, filenames=changed_filenames)

    code_files = [
        f
        for f in changed_filenames
        if (
            is_code_file(f)
            and not is_test_file(f)
            and not is_excluded_from_testing(f, coverage_data)
        )
    ]

    # If no code files were changed, return early
    if not code_files:
        return

    # Build the list of files to include in the issue
    files_to_test = []
    for file_path in code_files:
        # Check if we have coverage data for this file
        if file_path in coverage_data:
            file_info = coverage_data[file_path]
            file_entry = {"path": file_path}

            # Only add coverage data if it exists
            if "line_coverage" in file_info:
                file_entry["line_coverage"] = file_info["line_coverage"]
            if "function_coverage" in file_info:
                file_entry["function_coverage"] = file_info["function_coverage"]
            if "branch_coverage" in file_info:
                file_entry["branch_coverage"] = file_info["branch_coverage"]

            files_to_test.append(file_entry)
        else:
            # No coverage data for this file
            files_to_test.append({"path": file_path})

    # If no files need tests, return early
    if not files_to_test:
        return

    # Get PR creator to assign as reviewer
    pr_creator = pull_request["user"]["login"]
    assignees = (
        [pr_creator]
        if pr_creator and pr_creator != f"{PRODUCT_ID}-for-dev[bot]"
        else []
    )

    # Format files list for issue body
    file_list = []
    for file in files_to_test:
        path = file["path"]
        coverage_info = []

        if "line_coverage" in file:
            coverage_info.append(f"Line coverage: {file['line_coverage']}%")
        if "function_coverage" in file:
            coverage_info.append(f"Function coverage: {file['function_coverage']}%")
        if "branch_coverage" in file:
            coverage_info.append(f"Branch coverage: {file['branch_coverage']}%")

        if coverage_info:
            file_list.append(f"{path} ({', '.join(coverage_info)})")
        else:
            file_list.append(f"{path}")

    # Create issue title and body using templates
    title = get_issue_title_for_pr_merged(pr_number=pr_number)
    body = get_issue_body_for_pr_merged(pr_number=pr_number, file_list=file_list)

    # Create base args for issue creation
    base_args: BaseArgs = {
        "owner": owner,
        "repo": repo,
        "token": token,
    }

    # Create the issue
    create_issue(title=title, body=body, assignees=assignees, base_args=base_args)

    return None
