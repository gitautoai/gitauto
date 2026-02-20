# Local imports (Github)
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import GitHubInstallationPayload
from services.github.users.get_user_public_email import get_user_public_email

# Local imports (Supabase)
from services.supabase.credits.check_grant_exists import check_grant_exists
from services.supabase.credits.insert_credit import insert_credit
from services.supabase.installations.insert_installation import insert_installation
from services.supabase.owners.check_owner_exists import check_owner_exists
from services.supabase.owners.insert_owner import insert_owner
from services.supabase.users.upsert_user import upsert_user

# Local imports (Stripe)
from services.stripe.create_stripe_customer import create_stripe_customer

# Local imports (Others)
from services.webhook.process_repositories import process_repositories
from services.webhook.setup_handler import setup_handler
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import set_trigger


@handle_exceptions(raise_on_error=True)
async def handle_installation_created(payload: GitHubInstallationPayload):
    set_trigger("installation")
    installation_id = payload["installation"]["id"]
    owner = payload["installation"]["account"]
    owner_id = owner["id"]
    owner_name = owner["login"]
    owner_type = owner["type"]
    repositories = payload["repositories"]
    user_id = payload["sender"]["id"]
    user_name = payload["sender"]["login"]
    token = get_installation_access_token(installation_id=installation_id)
    email = get_user_public_email(username=user_name, token=token)

    if not check_owner_exists(owner_id=owner_id):
        customer_id = create_stripe_customer(
            owner_name=owner_name,
            owner_id=owner_id,
            installation_id=installation_id,
            user_id=user_id,
            user_name=user_name,
        )
        insert_owner(
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            user_id=user_id,
            user_name=user_name,
            stripe_customer_id=customer_id or "",
        )

    if not check_grant_exists(owner_id=owner_id):
        insert_credit(owner_id=owner_id, transaction_type="grant")

    insert_installation(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
    )

    upsert_user(user_id=user_id, user_name=user_name, email=email)

    await process_repositories(
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repositories=repositories,
        token=token,
        user_id=user_id,
        user_name=user_name,
    )

    # Auto-create coverage workflow PR when a single repo is installed
    if len(repositories) == 1:
        await setup_handler(
            owner_name=owner_name,
            repo_name=repositories[0]["name"],
            token=token,
        )
