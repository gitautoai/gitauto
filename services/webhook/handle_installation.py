from typing import Any
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import GitHubInstallationPayload
from services.github.users.get_user_public_email import get_user_public_email
from services.supabase.gitauto_manager import create_installation
from services.webhook.process_repositories import process_repositories
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_installation_created(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    owner_type: str = payload["installation"]["account"]["type"]
    owner_name: str = payload["installation"]["account"]["login"]
    owner_id: int = payload["installation"]["account"]["id"]
    repositories: list[dict[str, Any]] = payload["repositories"]
    user_id: int = payload["sender"]["id"]
    user_name: str = payload["sender"]["login"]
    token: str = get_installation_access_token(installation_id=installation_id)
    user_email: str | None = get_user_public_email(username=user_name, token=token)

    # Create installation record in Supabase
    create_installation(
        installation_id=installation_id,
        owner_type=owner_type,
        owner_name=owner_name,
        owner_id=owner_id,
        user_id=user_id,
        user_name=user_name,
        email=user_email,
    )

    # Process repositories
    process_repositories(
        owner_id=owner_id,
        owner_name=owner_name,
        repositories=repositories,
        token=token,
        user_id=user_id,
        user_name=user_name,
    )
