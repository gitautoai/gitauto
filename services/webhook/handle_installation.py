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
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_installation_created(payload: GitHubInstallationPayload):
    installation_id = payload["installation"]["id"]
    owner_type = payload["installation"]["account"]["type"]
    owner_name = payload["installation"]["account"]["login"]
    owner_id = payload["installation"]["account"]["id"]
    repositories = payload["repositories"]
    user_id = payload["sender"]["id"]
    user_name = payload["sender"]["login"]
    token = get_installation_access_token(installation_id=installation_id)
    if not token:
        return
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
            owner_type=owner_type,
            owner_name=owner_name,
            stripe_customer_id=customer_id,
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

    process_repositories(
        owner_id=owner_id,
        owner_name=owner_name,
        repositories=repositories,
        token=token,
        user_id=user_id,
        user_name=user_name,
    )
