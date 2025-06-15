import postgrest

# ... other imports and code ...

# Updated create_installation to handle duplicate installations gracefully

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
        # Improved error handling: try to update if duplicate key error
        error_data = None
        if hasattr(e, 'response'):
            try:
                error_data = e.response.json()
            except Exception:
                error_data = None
        if not error_data and e.args:
            error_data = e.args[0]
        if isinstance(error_data, dict) and error_data.get('code') == '23505':
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
