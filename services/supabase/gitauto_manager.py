from services.supabase.client import supabase


def create_installation(installation_id, owner_type, owner_name, owner_id, customer_id, user_id, user_name, email):
    # Insert or update owner record
    supabase.table(table_name="owners").insert(
        json={"owner_id": owner_id, "stripe_customer_id": customer_id},
        on_conflict="installation_id"
    ).execute()

    # Insert installation record
    supabase.table(table_name="installations").insert(
        json={
            "installation_id": installation_id,
            "owner_type": owner_type,
            "owner_id": owner_id,
        },
        on_conflict="installation_id"
    ).execute()

    # Additional logic may follow
    return True
