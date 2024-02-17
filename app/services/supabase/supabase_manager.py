from supabase import create_client, Client
import datetime


class InstallationTokenManager:
    def __init__(self, url, key):
        self.client: Client = create_client(url, key)

    def save_installation_token(self, installation_id, account_login, html_url, repositories):
        data = {
            "installation_id": installation_id,
            "login": account_login,
            'html_url': html_url,
            "repositories": repositories,
            "deleted_at": None,
        }
        response = self.client.table("repo_info").select("*").eq("installation_id", installation_id).execute()
        if(response[0]):
            self.client.table("repo_info").update(data).eq("installation_id", installation_id).execute()
        else:
            self.client.table("repo_info").insert(data).execute()
        return None

    def get_installation_token(self, installation_id):
        query = self.client.table("installation_tokens").select("access_token").eq("installation_id", installation_id)
        data = query.execute()
        if data.data and len(data.data) > 0:
            return data.data[0]['access_token']
        return None

    # Why this?
    def invalidate_installation_token(self, installation_id):
        data = {"access_token": ""}
        self.client.table("installation_tokens").update(data).eq("installation_id", installation_id).execute()

    def delete_installation_token(self, installation_id):
        data = {"deleted_at": datetime.datetime.utcnow().isoformat()}
        self.client.table("repo_info").update(data).eq("installation_id", installation_id).execute()
