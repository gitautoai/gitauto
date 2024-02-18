from supabase import create_client, Client


# Manager class to handle installation tokens
class InstallationTokenManager:
    # Initialize Supabase client when the manager is created
    def __init__(self, url, key):
        self.client: Client = create_client(url, key)

    # Save the installation token to the database
    def save_installation_token(self, installation_target_type, installation_target_id, installation_target_name, installation_id, installation_status, created_by_id, created_by_name):
        try:
            data = {
                "installation_target_type": installation_target_type,
                "installation_target_id": installation_target_id,
                "installation_target_name": installation_target_name,
                "installation_id": installation_id,
                "installation_status": installation_status,
                "created_by_id": created_by_id,
                "created_by_name": created_by_name,
            }
            self.client.table("installation_history").insert(data).execute()
            return None
        except Exception as e:
            print(f"Error saving installation token: {e}")

    # Get the installation token from the database
    def get_latest_installation_info(self, installation_target_type, installation_target_id):
        try:
            query = self.client.table("installation_view").select("*").eq("installation_target_type", installation_target_type).eq("installation_target_id", installation_target_id)
            data = query.execute()
            return data.data[0] if data.data else None
        except Exception as e:
            print(f"Error getting installation token: {e}")
            return None
