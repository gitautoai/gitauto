from services.supabase.client import supabase
import postgrest
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def create_installation(installation_id, owner_type, owner_name, owner_id, user_id, user_name, email):
    """Create a new installation record, or update the existing one if it already exists."""
    installation_data = {
        "installation_id": installation_id,
        "owner_type": owner_type,
        "owner_name": owner_name,
        "owner_id": owner_id,
        "user_id": user_id,
        "user_name": user_name,
        "email": email,
        "uninstalled_at": None
    }
    
    try:
        # Try to update first
        response = (
            supabase.table("installations")
            .upsert(
                installation_data,
                on_conflict="installation_id"
            )
            .execute()
        )
        return response
    except Exception as e:
        # If there's still an error that's not related to duplicate keys, raise it
        if not (isinstance(e.args[0], dict) and e.args[0].get('code') == '23505'):
            raise
        # If we get here with a duplicate key error, something unexpected happened
        raise RuntimeError(f"Failed to upsert installation {installation_id}: {str(e)}")


@handle_exceptions(default_return_value=None, raise_on_error=True)
def create_user_request(user_id: int,
                         user_name: str,
                         installation_id: int,
                         owner_id: int,
                         owner_type: str,
                         owner_name: str,
                         repo_id: int,
                         repo_name: str,
                         issue_number: int,
                         source: str,
                         email: str | None) -> int:
    data, _ = (
        supabase.table("usage")
        .insert(
            json={
                "user_id": user_id,
                "user_name": user_name,
                "installation_id": installation_id,
                "owner_id": owner_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "issue_number": issue_number,
                "source": source,
                "email": email,
                "is_completed": False
            }
        )
        .execute()
    )
    supabase.table("users").upsert(
        json={
            "user_id": user_id,
            "user_name": user_name,
            "email": email,
            "installation_id": installation_id,
        }
    ).execute()
    return data[1][0]["id"]
