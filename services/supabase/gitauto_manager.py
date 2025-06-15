from services.supabase.client import supabase
import postgrest
from services.supabase.users_manager import upsert_user


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