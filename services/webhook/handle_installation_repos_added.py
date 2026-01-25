from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import GitHubInstallationRepositoriesPayload
from services.supabase.installations.is_installation_valid import is_installation_valid
from services.webhook.process_repositories import process_repositories
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
async def handle_installation_repos_added(
    payload: GitHubInstallationRepositoriesPayload,
):
    installation_id = payload["installation"]["id"]
    if not is_installation_valid(installation_id=installation_id):
        return

    token = get_installation_access_token(installation_id=installation_id)

    # Get other information
    owner = payload["installation"]["account"]
    owner_id = owner["id"]
    owner_name = owner["login"]
    owner_type = owner["type"]
    sender_id = payload["sender"]["id"]
    sender_name = payload["sender"]["login"]

    # Process added repositories
    await process_repositories(
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repositories=payload["repositories_added"],
        token=token,
        user_id=sender_id,
        user_name=sender_name,
    )
