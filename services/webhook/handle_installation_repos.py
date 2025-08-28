from services.github.token.get_installation_token import get_installation_access_token
from services.supabase.installations.is_installation_valid import is_installation_valid
from services.webhook.process_repositories import process_repositories
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_installation_repos_added(payload) -> None:
    installation_id: int = payload["installation"]["id"]
    if not is_installation_valid(installation_id=installation_id):
        return
    token: str = get_installation_access_token(installation_id=installation_id)

    # Get other information
    owner_id = payload["installation"]["account"]["id"]
    owner_name = payload["installation"]["account"]["login"]
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]

    # Process added repositories
    process_repositories(
        owner_id=owner_id,
        owner_name=owner_name,
        repositories=payload["repositories_added"],
        token=token,
        user_id=sender_id,
        user_name=sender_name,
    )
