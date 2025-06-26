# Standard imports
import logging

# Local imports (AWS)
from services.aws.types.schedule_event import ScheduleEvent

# Local imports (GitHub)
from services.github.github_types import BaseArgs
from services.github.issues.create_issue import create_issue
from services.github.issues.is_issue_open import is_issue_open
from services.github.token.get_installation_token import get_installation_access_token

# Local imports (Supabase)
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.supabase.coverages.update_issue_url import update_issue_url
from services.supabase.installations.get_installation_id import get_installation_id
from services.supabase.repositories.get_repository import get_repository_settings
from services.supabase.users_manager import get_how_many_requests_left_and_cycle

# Local imports (Utils)
from utils.issue_templates.schedule import get_issue_title, get_issue_body
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_excluded_from_testing import is_excluded_from_testing
from utils.files.is_test_file import is_test_file


@handle_exceptions(default_return_value=None, raise_on_error=False)
def schedule_handler(event: ScheduleEvent, _context):
    # Extract details from the event payload
    detail = event.get("detail", {})
    owner_id = detail.get("ownerId")
    owner_type = detail.get("ownerType")
    owner_name = detail.get("ownerName")
    repo_id = detail.get("repoId")
    repo_name = detail.get("repoName")

    if not owner_id or not owner_name or not owner_type or not repo_id or not repo_name:
        logging.error("Missing required fields in event detail")
        return

    # Get repository settings - check if trigger_on_schedule is enabled
    repo_settings = get_repository_settings(repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_schedule", False):
        msg = f"Skipping repo_id: {repo_id} - trigger_on_schedule is not enabled"
        logging.info(msg)
        return

    # Get installation access token
    installation_id = get_installation_id(owner_id=owner_id)
    token = get_installation_access_token(installation_id=installation_id)
    if token is None:
        logging.error("Token is None for installation_id: %s", installation_id)
        return

    # Check the remaining available usage count
    requests_left, _request_count, _end_date, _is_retried = (
        get_how_many_requests_left_and_cycle(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=None,
        )
    )
    if requests_left < 1:
        logging.info("No requests left for %s/%s", owner_name, repo_name)
        return

    # Get all coverage records for the repository
    all_coverages = get_all_coverages(repo_id=repo_id)
    if not all_coverages:
        logging.info("No coverage data found for %s/%s", owner_name, repo_name)
        return

    # Create a coverage dict for is_excluded_from_testing function
    coverage_dict = {item["full_path"]: item for item in all_coverages}

    # Find the first suitable file
    target_file = None
    for coverage_record in all_coverages:
        file_path = coverage_record["full_path"]

        # Skip non-code files
        if not is_code_file(file_path):
            continue

        # Skip test files
        if is_test_file(file_path):
            continue

        # Skip files excluded from testing
        if is_excluded_from_testing(file_path, coverage_dict):
            continue

        # Skip files that have open GitHub issues
        github_issue_url = coverage_record.get("github_issue_url")
        if github_issue_url and is_issue_open(issue_url=github_issue_url, token=token):
            continue

        # Found a suitable file
        target_file = coverage_record
        break

    if target_file is None:
        logging.info("No suitable coverage file found for %s/%s", owner_name, repo_name)
        return

    file_path = target_file["full_path"]
    statement_coverage = target_file.get("statement_coverage")

    # Create issue title and body
    title = get_issue_title()
    body = get_issue_body(file_path=file_path, statement_coverage=statement_coverage)

    # Create base args for issue creation
    base_args: BaseArgs = {
        "owner": owner_name,
        "repo": repo_name,
        "token": token,
    }

    # Create the issue with gitauto label
    issue_response = create_issue(
        title=title, body=body, assignees=[], base_args=base_args
    )

    if issue_response and "html_url" in issue_response:
        update_issue_url(
            repo_id=repo_id,
            file_path=file_path,
            github_issue_url=issue_response["html_url"],
        )

    return
