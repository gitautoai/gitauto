from config import PRODUCT_ID
from services.github.issues.create_issue import create_issue
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import GitHubPullRequestClosedPayload, BaseArgs
from services.slack.slack_notify import slack_notify
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.repositories.get_repository import get_repository
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_excluded_from_testing import is_excluded_from_testing
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file
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
    owner_name = repository["owner"]["login"]
    repo_id = repository["id"]
    repo_name = repository["name"]
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)

    # Get repository settings
    repo_settings = get_repository(repo_id=repo_id)
    if not repo_settings or not repo_settings["trigger_on_merged"]:
        return None

    # Get PR number and details
    pr_number = payload["number"]
    pull_request = payload["pull_request"]
    pull_url = pull_request["url"]

    # Start notification
    start_msg = f"PR merged handler started: PR #{pr_number} merged in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)

    # Get files changed in the PR
    pull_files_url = f"{pull_url}/files"
    changed_files = get_pull_request_files(url=pull_files_url, token=token)

    # Filter for code files that might need tests
    coverage_data = get_coverages(
        repo_id=repo_id, filenames=[f["filename"] for f in changed_files]
    )

    changed_code_files = [
        f
        for f in changed_files
        if (
            is_code_file(filename=f["filename"])
            and not is_test_file(filename=f["filename"])
            and not is_type_file(filename=f["filename"])
            and not is_excluded_from_testing(
                filename=f["filename"], coverage_data=coverage_data
            )
        )
    ]

    # If no code files were changed, return early
    if not changed_code_files:
        # Early return notification
        early_return_msg = (
            f"No code files changed in PR #{pr_number} for {owner_name}/{repo_name}"
        )
        slack_notify(early_return_msg, thread_ts)
        return None

    # Build the list of files to include in the issue
    files_to_test = []
    for file in changed_code_files:
        # Check if we have coverage data for this file
        if file["filename"] in coverage_data:
            file_info = coverage_data[file["filename"]]
            file_entry = {"path": file["filename"]}

            # Only add coverage data if it exists
            if file_info["line_coverage"] is not None:
                file_entry["line_coverage"] = file_info["line_coverage"]
            if file_info["function_coverage"] is not None:
                file_entry["function_coverage"] = file_info["function_coverage"]
            if file_info["branch_coverage"] is not None:
                file_entry["branch_coverage"] = file_info["branch_coverage"]

            files_to_test.append(file_entry)
        else:
            # No coverage data for this file
            files_to_test.append({"path": file["filename"]})

    # If no files need tests, return early
    if not files_to_test:
        # Early return notification
        early_return_msg = (
            f"No files need tests in PR #{pr_number} for {owner_name}/{repo_name}"
        )
        slack_notify(early_return_msg, thread_ts)
        return None

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
    base_args: BaseArgs = {"owner": owner_name, "repo": repo_name, "token": token}

    # Create the issue
    issue_response = create_issue(
        title=title, body=body, assignees=assignees, base_args=base_args
    )

    if issue_response and "html_url" in issue_response:
        # Success notification
        success_msg = f"Issue created for PR #{pr_number} in {owner_name}/{repo_name}"
        slack_notify(success_msg, thread_ts)
    else:
        # Failure notification
        failure_msg = f"@channel Failed to create issue for PR #{pr_number} in {owner_name}/{repo_name}"
        slack_notify(failure_msg, thread_ts)

    # End notification
    end_msg = "Completed" if issue_response else "@channel Failed"
    slack_notify(end_msg, thread_ts)

    return None
