from services.supabase.client import supabase
import postgrest

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
    except postgrest.exceptions.APIError as e:
        # If there's still an error that's not related to duplicate keys, raise it
        if not (isinstance(e.args[0], dict) and e.args[0].get('code') == '23505'):
            raise
        # If we get here with a duplicate key error, something unexpected happened
        raise RuntimeError(f"Failed to upsert installation {installation_id}: {str(e)}")