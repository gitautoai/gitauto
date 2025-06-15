# Standard imports
from typing import Any, List, Optional

# Third party imports
import postgrest

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


def create_installation(
    installation_id: int,
    owner_type: str,
    owner_name: str,
    owner_id: int,
    user_id: int,
    user_name: str,
    email: Optional[str]
) -> dict[str, Any]:
    """Create a new installation record, or update the existing one if it already exists."""
    try:
        # Import locally to avoid circular dependency
        from services.supabase.users_manager import upsert_user

        # First create/update the user record with the email
        upsert_user(user_id=user_id, user_name=user_name, email=email)
        
        # Then create the installation record
        response = (
            supabase.table("installations")
            .insert({
                "installation_id": installation_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "owner_id": owner_id,
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
                    "uninstalled_at": None
                })
                .eq("installation_id", installation_id)
                .execute()
            )
            return response
        else:
            raise


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
    email: Optional[str]
) -> int:
    """Creates record in usage table for this user and issue."""
    # Import locally to avoid circular dependency
    from services.supabase.users_manager import upsert_user
    
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
def get_installation_id(owner_id: int) -> Optional[int]:
    """https://supabase.com/docs/reference/python/is"""
    data, _ = (
        supabase.table("installations")
        .select("installation_id")
        .eq("owner_id", owner_id)
        .is_("uninstalled_at", "null")  # Not uninstalled
        .execute()
    )
    # Return the first installation id even if there are multiple installations
    return data[1][0]["installation_id"] if data[1] else None


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_ids() -> List[int]:
    """https://supabase.com/docs/reference/python/is"""
    data, _ = (
        supabase.table("installations")
        .select("installation_id")
        .is_("uninstalled_at", "null")  # Not uninstalled
        .execute()
    )
    return [item["installation_id"] for item in data[1]]


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_users_first_issue(user_id: int, installation_id: int) -> bool:
    """Check if this is the user's first issue by verifying if there are no completed usage records for the given user_id and installation_id."""
    data, _ = (
        supabase.table("usage")
        .select("*")
        .eq("user_id", user_id)
        .eq("installation_id", installation_id)
        .eq("is_completed", True)
        .execute()
    )
    return len(data[1]) == 0


@handle_exceptions(default_return_value=None, raise_on_error=False)
def set_issue_to_merged(
    owner_type: str,
    owner_name: str,
    repo_name: str,
    issue_number: int
) -> None:
    """Set the merged flag to True for the specified issue."""
    (
        supabase.table("issues")
        .update(json={"merged": True})
        .eq("owner_type", owner_type)
        .eq("owner_name", owner_name)
        .eq("repo_name", repo_name)
        .eq("issue_number", issue_number)
        .execute()
    )
