from services.supabase.client import supabase
import postgrest
from services.supabase.users_manager import upsert_user
from utils.error.handle_exceptions import handle_exceptions


def create_installation(installation_id, owner_type, owner_name, owner_id, user_id, user_name, email):
    """Create a new installation record, or update the existing one if it already exists."""
    try:
        # First create/update the user record with the email
        upsert_user(user_id=user_id, user_name=user_name, email=email)
        
        # Then create the installation record without the email field
        response = (
            supabase.table("installations")
            .insert({
                "installation_id": installation_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "owner_id": owner_id,
                "user_id": user_id,
                "user_name": user_name,
                "uninstalled_at": None
            })
            .execute()
        )
        return response
    except postgrest.exceptions.APIError as e:
        error = e.args[0] if e.args else {}
        # If duplicate key error, perform update instead
        if isinstance(error, dict) and error.get('code') == '23505':
            response = (
                supabase.table("installations")
                .update({
                    "owner_type": owner_type,
                    "owner_name": owner_name,
                    "owner_id": owner_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "uninstalled_at": None
                })
                .eq("installation_id", installation_id)
def is_users_first_issue(user_id, installation_id):
    """Check if this is the user's first issue by verifying if there are no completed usage records for the given user_id and installation_id."""
    data, _ = supabase.table("usage")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("installation_id", installation_id)\
        .eq("is_completed", True)\
        .execute()
    return len(data[1]) == 0
                .execute()
            )
            return response
        else:
            raise


def create_user_request(user_id, user_name, installation_id, owner_id, owner_type, owner_name, repo_id, repo_name, issue_number, source, email):
    """Creates record in usage table for this user and issue."""
    # First create/update the user record with the email
    upsert_user(user_id=user_id, user_name=user_name, email=email)
    
    # Check if issue exists
    data, _ = (
        supabase.table("issues")
        .select("*")
        .eq("owner_type", owner_type)
        .eq("owner_name", owner_name)
        .eq("repo_name", repo_name)
        .eq("issue_number", issue_number)
        .execute()
    )
    
    # Create issue if it doesn't exist
    if not data[1]:
        supabase.table("issues").insert(
            json={
                "owner_id": owner_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "issue_number": issue_number,
            }
        ).execute()
    
    # Create usage record
    data, _ = (
        supabase.table("usage")
        .insert(
            json={
                "user_id": user_id,
                "installation_id": installation_id,
                "owner_id": owner_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "issue_number": issue_number,
                "source": source,
            }
        )
        .execute()
    )
    
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
