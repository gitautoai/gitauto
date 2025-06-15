from services.stripe.customer import create_stripe_customer, subscribe_to_free_plan
from services.supabase.client import supabase
import postgrest


def create_installation(installation_id, owner_type, owner_name, owner_id, user_id, user_name, email):
    """Create a new installation record, or update the existing one if it already exists."""
    existing, _ = supabase.table("installations")\
        .select("installation_id")\
        .eq("installation_id", installation_id)\
        .execute()
    if existing[1] and len(existing[1]) > 0:
        response = supabase.table("installations")\
            .update({
                "owner_type": owner_type,
                "owner_name": owner_name,
                "owner_id": owner_id,
                "user_id": user_id,
                "user_name": user_name,
                "email": email,
                "uninstalled_at": None
            })\
            .eq("installation_id", installation_id)\
            .execute()
        return response
    else:
        response = supabase.table("installations")\
            .insert({
                "installation_id": installation_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "owner_id": owner_id,
                "user_id": user_id,
                "user_name": user_name,
                "email": email,
                "uninstalled_at": None
            })\
            .execute()
        return response


# ... other functions ...
