from services.supabase.client import supabase
import postgrest
from utils.error.handle_exceptions import handle_exceptions


def create_installation(
    installation_id, owner_type, owner_name, owner_id, user_id, user_name, email
):
    """Create a new installation record, or update the existing one if it already exists."""
    # Check if installation record already exists
    existing_installation, _ = supabase.table(table_name="installations") \
        .select("installation_id, uninstalled_at") \
        .eq(column="installation_id", value=installation_id) \
        .execute()
    if existing_installation[1]:
        supabase.table(table_name="installations").update(
            json={
                "owner_name": owner_name,
                "owner_type": owner_type,
                "owner_id": owner_id,
                "uninstalled_at": None
            }
        ).eq("installation_id", installation_id).execute()
    else:
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


def upsert_user(user_id, user_name, email=None):
    """Create a new user record, or update the existing one if it already exists."""
    supabase.table(table_name="users").upsert(
        json={
            "user_id": user_id,
            "user_name": user_name,
            "email": email,
        }
    ).execute()


@handle_exceptions(default_return_value=None, raise_on_error=True)
def create_user_request(
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