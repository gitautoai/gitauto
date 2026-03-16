from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import InstallationRepositoriesPayload
from services.github.users.get_email_from_commits import get_email_from_commits
from services.github.users.get_user_public_email import get_user_public_info
from services.supabase.installations.is_installation_valid import is_installation_valid
from services.supabase.users.upsert_user import upsert_user
from services.webhook.process_repositories import process_repositories
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import set_trigger


@handle_exceptions(raise_on_error=True)
def handle_installation_repos_added(
    payload: InstallationRepositoriesPayload,
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

    # Capture sender's email (this sender may differ from the original installer)
    sender_info = get_user_public_info(username=sender_name, token=token)
    if not sender_info.email and repositories:
        for repo in repositories:
            email = get_email_from_commits(
                owner=owner_name, repo=repo["name"], username=sender_name, token=token
            )
            if email:
                sender_info.email = email
                break
    upsert_user(
        user_id=sender_id,
        user_name=sender_name,
        email=sender_info.email,
        display_name=sender_info.display_name,
    )
    process_repositories(
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repositories=repositories,
        token=token,
        user_id=sender_id,
        user_name=sender_name,
        installation_id=installation_id,
        sender_email=sender_info.email,
        sender_display_name=sender_info.display_name,
    )

    # Don't auto-trigger setup_handler here. When users add many repos at once, GitHub sends a separate webhook per repo, each with len(repositories_added)==1, which would create coverage PRs for every repo. Users can trigger setup from the website button instead.
