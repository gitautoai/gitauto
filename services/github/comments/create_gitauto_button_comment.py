from constants.messages import CLICK_THE_CHECKBOX
from services.github.comments.combine_and_create_comment import combine_and_create_comment
from services.github.github_manager import get_user_public_email
from services.github.github_types import GitHubLabeledPayload
from services.github.token.get_installation_token import get_installation_access_token
from services.supabase.gitauto_manager import is_users_first_issue
from services.supabase.users.upsert_user import upsert_user
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_gitauto_button_comment(payload: GitHubLabeledPayload) -> None:
    """Create a comment with GitAuto button and usage information"""
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)
    owner_id: int = payload["repository"]["owner"]["id"]
    owner_name: str = payload["repository"]["owner"]["login"]
    owner_type: str = payload["repository"]["owner"]["type"]
    repo_name: str = payload["repository"]["name"]
    issue_number: int = payload["issue"]["number"]
    user_id: int = payload["sender"]["id"]
    user_name: str = payload["sender"]["login"]
    user_email: str | None = get_user_public_email(username=user_name, token=token)

    # Create user if not exist and check if first issue
    upsert_user(user_id=user_id, user_name=user_name, email=user_email)
    first_issue = is_users_first_issue(user_id=user_id, installation_id=installation_id)

    # Base comment
    base_comment = f"{CLICK_THE_CHECKBOX}\n- [ ] Generate PR"

    # Create base args for comment creation
    base_args = {
        "owner": owner_name,
        "repo": repo_name,
        "issue_number": issue_number,
        "token": token,
    }

    # Create the comment with usage info
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repo_name=repo_name,
        issue_number=issue_number,
        sender_name=user_name,
        base_args=base_args,
        welcome_message=first_issue,
    )
