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

    # Insert installation record
    supabase.table(table_name="installations").insert(
        json={
            "installation_id": installation_id,
            "owner_name": owner_name,
            "owner_type": owner_type,
            "owner_id": owner_id,
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
                "installation_id": installation_id,
            }
        ).execute()

    # Add user request to usage table
    data, _ = (
        supabase.table(table_name="usage")
        .insert(
            json={
                "owner_id": owner_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "issue_number": issue_number,
                "user_id": user_id,
                "installation_id": installation_id,
                "source": source,
            }
        )
        .execute()
    )

    # Upsert user
    upsert_user(user_id=user_id, user_name=user_name, email=email)

    return data[1][0]["id"]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_id(owner_id: int) -> int:
    """https://supabase.com/docs/reference/python/is"""
    data, _ = (
        supabase.table(table_name="installations")
        .select("installation_id")
        .eq(column="owner_id", value=owner_id)
        .is_(column="uninstalled_at", value="null")  # Not uninstalled
        .execute()
    )
    # Return the first installation id even if there are multiple installations
    return data[1][0]["installation_id"]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_ids() -> list[int]:
    """https://supabase.com/docs/reference/python/is"""
    data, _ = (
        supabase.table(table_name="installations")
        .select("installation_id")
        .is_(column="uninstalled_at", value="null")  # Not uninstalled
        .execute()
    )
    return [item["installation_id"] for item in data[1]]


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_users_first_issue(user_id: int, installation_id: int) -> bool:
    # Check if there are any completed usage records for this user and installation
    data, _ = (
        supabase.table(table_name="usage")
        .select("*")
        .eq(column="user_id", value=user_id)
        .eq(column="installation_id", value=installation_id)
        .eq(column="is_completed", value=True)
        .execute()
    )
    return len(data[1]) == 0


@handle_exceptions(default_return_value=None, raise_on_error=False)
def set_issue_to_merged(
    owner_type: str, owner_name: str, repo_name: str, issue_number: int
) -> None:
    (
        supabase.table(table_name="issues")
        .update(json={"merged": True})
        .eq(column="owner_type", value=owner_type)
        .eq(column="owner_name", value=owner_name)
        .eq(column="repo_name", value=repo_name)
        .eq(column="issue_number", value=issue_number)
        .execute()
    )
