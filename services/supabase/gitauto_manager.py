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
        response = (
            supabase.table("installations")
            .insert(installation_data, upsert=True)
            .execute()
        )
        return response
    except postgrest.exceptions.APIError as e:
        raise RuntimeError(f"Failed to upsert installation {installation_id}: {str(e)}")

# ... other functions ...
