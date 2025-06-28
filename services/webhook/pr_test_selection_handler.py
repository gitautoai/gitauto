# Standard imports
import logging

# Local imports (Services)
from services.github.comments.create_comment import create_comment
from services.github.pull_requests.get_pull_request_files import get_pull_request_files
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.pull_request_webhook_payload import PullRequestWebhookPayload
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.repositories.get_repository import get_repository_settings
from services.webhook.utils.create_file_checklist import create_file_checklist
from services.webhook.utils.create_test_selection_comment import (
    create_test_selection_comment,
)

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_test_file import is_test_file


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_pr_test_selection(payload: PullRequestWebhookPayload):
    # Skip if the PR is from a bot
    pull_request = payload["pull_request"]
    sender_name = payload["sender"]["login"]
    if sender_name.endswith("[bot]"):
        msg = f"Skipping PR test selection for bot {sender_name}"
        logging.info(msg)
        return

    # Extract repository related variables
    repo = payload["repository"]
    repo_id = repo["id"]
    repo_name = repo["name"]

    # Check repository settings for PR test selection
    repo_settings = get_repository_settings(repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_pr_change", False):
        msg = f"Skipping PR test selection for repo {repo_name} because trigger_on_pr_change is False"
        logging.info(msg)
        return

    # Extract owner related variables
    owner = repo["owner"]
    owner_name = owner["login"]

    # Extract PR related variables
    pull_number = pull_request["number"]
    pull_url = pull_request["url"]
    pull_files_url = f"{pull_url}/files"

    # Extract other information
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)

    # Get files changed in the PR
    changed_filenames = get_pull_request_files(url=pull_files_url, token=token)

    # If no code files were changed, return early
    code_files = [
        f for f in changed_filenames if is_code_file(f) and not is_test_file(f)
    ]
    if not code_files:
        msg = f"Skipping PR test selection for repo {repo_name} because no code files were changed"
        logging.info(msg)
        return

    # Filter for code files that might need tests
    coverage_data = get_coverages(repo_id=repo_id, filenames=changed_filenames)

    checklist = create_file_checklist(code_files, coverage_data)
    comment_body = create_test_selection_comment(checklist)

    # Create base args for comment creation
    base_args = {
        "owner": owner_name,
        "repo": repo_name,
        "issue_number": pull_number,
        "token": token,
    }

    # Create the comment
    create_comment(body=comment_body, base_args=base_args)
