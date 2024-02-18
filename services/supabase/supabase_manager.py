from supabase import create_client, Client


# Manager class to handle installation tokens
class InstallationTokenManager:
    # Initialize Supabase client when the manager is created
    def __init__(self, url, key):
        self.client: Client = create_client(url, key)

    def save_installation_token(self, installation_id, account_login, html_url, repositories, repository_ids):
        data, _ = self.client.table("repo_info").select("*").eq("installation_id", installation_id).execute()
        if (len(data[1]) > 0):
            self.client.table("repo_info").update({
            "installation_id": installation_id,
            "login": account_login,
            'html_url': html_url,
            "repositories": repositories,
            "repository_ids": repository_ids,
            "deleted_at": None,
        }).eq("installation_id", installation_id).execute()
        else:
                self.client.table("repo_info").insert({
            "installation_id": installation_id,
            "login": account_login,
            'html_url': html_url,
            "repositories": repositories,
            "repository_ids": repository_ids,
        }).execute()

    # Save the installation token to the database
    def save_installation_info(self, installation_target_type, installation_target_id, installation_target_name, installation_id, installation_status, created_by_id, created_by_name):
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

    def get_installation_id(self, repository_id):
        data, _ = self.client.table("repo_info").select("installation_id").contains('repository_ids', [str(repository_id)]).execute()
        if (data[1] and data[0][1]):
            return data[1][0].get('installation_id')
        raise RuntimeError("Installation ID for this repo not found.")
