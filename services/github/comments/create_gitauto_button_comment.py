from constants.messages import CLICK_THE_CHECKBOX
from services.github.comments.combine_and_create_comment import (
    combine_and_create_comment,
)
from services.github.types.github_types import GitHubLabeledPayload
from services.github.token.get_installation_token import get_installation_access_token
from services.github.users.get_user_public_email import get_user_public_email
from services.supabase.users.upsert_user import upsert_user
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_gitauto_button_comment(payload: GitHubLabeledPayload) -> None:
    """Create a comment with GitAuto button and usage information"""
    installation_id: int = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)
    owner_id = payload["repository"]["owner"]["id"]
    owner_name = payload["repository"]["owner"]["login"]
    repo_name = payload["repository"]["name"]
    issue_number = payload["issue"]["number"]
    user_id = payload["sender"]["id"]
    user_name = payload["sender"]["login"]
    user_email = get_user_public_email(username=user_name, token=token)

    # Create user if not exist and check if first issue
    upsert_user(user_id=user_id, user_name=user_name, email=user_email)

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
        sender_name=user_name,
        base_args=base_args,
    )
