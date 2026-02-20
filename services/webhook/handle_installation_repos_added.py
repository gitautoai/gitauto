from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import GitHubInstallationRepositoriesPayload
from services.supabase.installations.is_installation_valid import is_installation_valid
from services.webhook.process_repositories import process_repositories
from services.webhook.setup_handler import setup_handler
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import set_trigger


@handle_exceptions(raise_on_error=True)
async def handle_installation_repos_added(
    payload: GitHubInstallationRepositoriesPayload,
):
    set_trigger("installation_repositories")
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
    repositories = payload["repositories_added"]
    await process_repositories(
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repositories=repositories,
        token=token,
        user_id=sender_id,
        user_name=sender_name,
    )

    # Auto-create coverage workflow PR when a single repo is added
    if repositories and len(repositories) == 1:
        await setup_handler(
            owner_name=owner_name,
            repo_name=repositories[0]["name"],
            token=token,
        )
