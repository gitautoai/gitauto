# Standard imports
import logging

# Local imports (Services)
from services.github.comments.combine_and_create_comment import (
    combine_and_create_comment,
)
from services.github.comments.delete_comments_by_identifiers import (
    delete_comments_by_identifiers,
)
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.pull_request_webhook_payload import PullRequestWebhookPayload
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.repositories.get_repository import get_repository
from services.webhook.utils.create_file_checklist import create_file_checklist
from services.webhook.utils.create_test_selection_comment import (
    create_test_selection_comment,
)

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_pr_checkbox_comment(payload: PullRequestWebhookPayload):
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
    repo_settings = get_repository(repo_id=repo_id)
    if not repo_settings or not repo_settings["trigger_on_pr_change"]:
        msg = f"Skipping PR test selection for repo {repo_name} because trigger_on_pr_change is False"
        logging.info(msg)
        return

    # Extract owner related variables
    owner = repo["owner"]
    owner_id = owner["id"]
    owner_name = owner["login"]

    # Extract PR related variables
    pull_number = pull_request["number"]
    pull_url = pull_request["url"]
    pull_files_url = f"{pull_url}/files"

    # Extract other information
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)

    # Get files changed in the PR
    changed_files = get_pull_request_files(url=pull_files_url, token=token)

    # Filter for code files only
    changed_code_files = [
        f
        for f in changed_files
        if is_code_file(f["filename"])
        and not is_test_file(f["filename"])
        and not is_type_file(f["filename"])
    ]

    if not changed_code_files:
        msg = f"Skipping PR test selection for repo {repo_name} because no code files were changed"
        logging.info(msg)
        return

    # Get coverage data for the changed files
    changed_file_paths = [f["filename"] for f in changed_code_files]
    coverage_data = get_coverages(repo_id=repo_id, filenames=changed_file_paths)

    checklist = create_file_checklist(changed_code_files, coverage_data)

    # Get branch name for reset command
    branch_name = pull_request["head"]["ref"]
    base_comment = create_test_selection_comment(checklist, branch_name)

    # Create base args for comment creation
    base_args = {
        "owner": owner_name,
        "repo": repo_name,
        "issue_number": pull_number,
        "token": token,
    }

    # Delete existing test selection comments before creating new one
    delete_comments_by_identifiers(
        base_args=base_args, identifiers=[TEST_SELECTION_COMMENT_IDENTIFIER]
    )

    # Combine and create the comment
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        sender_name=sender_name,
        base_args=base_args,
    )
