def create_installation(installation_id, owner_type, owner_name, owner_id, customer_id):
    # Insert owner record
    supabase.table(table_name="owners").insert(
        json={"owner_id": owner_id, "stripe_customer_id": customer_id}, on_conflict="installation_id"
    ).execute()

    # Insert installation record
    supabase.table(table_name="installations").upsert(
        json={
            "id": installation_id,
            "installation_id": installation_id,
            "owner_name": owner_name,
            "owner_type": owner_type,
            "owner_id": owner_id,
        }, on_conflict="installation_id"
    ).execute()

    # Upsert user
    # ... rest of the function implementation
    pass
