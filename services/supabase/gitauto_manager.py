from services.stripe.customer import create_stripe_customer, subscribe_to_free_plan
from services.supabase.client import supabase
from services.supabase.users_manager import upsert_user
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def create_installation(
    installation_id: int,
    owner_type: str,
    owner_name: str,
    owner_id: int,
    user_id: int,
    user_name: str,
    email: str | None,
) -> None:
    """Create owners record with stripe customerId, subscribe to free plan, create installation record, create users record on Installation Webhook event"""
    # If owner doesn't exist in owners table, insert owner and stripe customer
    data, _ = (
        supabase.table(table_name="owners")
        .select("owner_id")
        .eq(column="owner_id", value=owner_id)
        .execute()
    )
    if not data[1]:
        customer_id = create_stripe_customer(
            owner_name=owner_name,
            owner_id=owner_id,
            installation_id=installation_id,
            user_id=user_id,
            user_name=user_name,
        )
        subscribe_to_free_plan(
            customer_id=customer_id,
            owner_id=owner_id,
            owner_name=owner_name,
            installation_id=installation_id,
        )
        supabase.table(table_name="owners").insert(
            json={"owner_id": owner_id, "stripe_customer_id": customer_id}
        ).execute()

    # Insert installation record only if it does not exist
    data_inst, _ = (
        supabase.table(table_name="installations")
        .select("installation_id")
        .eq("installation_id", installation_id)
        .execute()
    )
    if not data_inst[1]:
        supabase.table(table_name="installations").insert(
            json={
                "installation_id": installation_id,
                "owner_name": owner_name,
                "owner_type": owner_type,
                "owner_id": owner_id
            }
        ).execute()

    # Upsert user
    upsert_user(user_id=user_id, user_name=user_name, email=email)


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def create_user_request(
    user_id: int,
    user_name: str,
    installation_id: int,
    owner_id: int,
    owner_type: str,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    issue_number: int,
    source: str,
    email: str | None,
) -> int:
    """Creates record in usage table for this user and issue."""
    # If issue doesn't exist, create one
    data, _ = (
        supabase.table(table_name="issues")
        .select("*")
        .eq(column="owner_type", value=owner_type)
        .eq(column="owner_name", value=owner_name)
        .eq(column="repo_name", value=repo_name)
        .eq(column="issue_number", value=issue_number)
        .execute()
    )

    # If no issue exists with those identifiers, create one
    if not data[1]:
        supabase.table(table_name="issues").insert(
            json={
                "owner_id": owner_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "issue_number": issue_number,
                "source": source
            }
        ).execute()

    # Upsert usage record
    data_usage, _ = supabase.table(table_name="usage").select("*").eq("user_id", user_id).execute()
    if data_usage and data_usage[0]:
        # Update existing usage record
        supabase.table(table_name="usage").update(
            json={"source": source}
        ).eq("user_id", user_id).execute()
    else:
        # Insert new usage record
        data_insert, _ = supabase.table(table_name="usage").insert(
            json={
                "user_id": user_id,
                "installation_id": installation_id,
                "repo_id": repo_id,
                "issue_number": issue_number,
                "source": source,
            }
