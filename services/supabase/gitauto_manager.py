from services.supabase.client import supabase


def create_installation(installation_id, owner_name, owner_type, owner_id):
    # Some previous code
    # Insert installation record
    supabase.table(table_name="installations").upsert(
        json={
            "installation_id": installation_id,
            "owner_name": owner_name,
            "owner_type": owner_type,
            "owner_id": owner_id
        },
        on_conflict="installation_id"
    ).execute()
    # Rest of the function
