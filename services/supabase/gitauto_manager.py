from services.supabase.client import supabase
import postgrest


def create_installation(installation_id, owner_type, owner_name, owner_id, user_id, user_name, email):
    """Create a new installation record, or update the existing one if it already exists."""
    try:
        response = (
            supabase.table("installations")
            .insert({
                "installation_id": installation_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "owner_id": owner_id,
                "user_id": user_id,
                "user_name": user_name,
                "email": email,
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
                    "email": email,
                    "uninstalled_at": None
                })
                .eq("installation_id", installation_id)
                .execute()
            )
            return response
        else:
            raise


# ... other functions ...
