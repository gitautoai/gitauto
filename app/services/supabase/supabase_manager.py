from supabase import create_client, Client
import datetime


class InstallationTokenManager:
    def __init__(self, url, key):
        self.client: Client = create_client(url, key)

    # Save the installation token to the database
    def save_installation_token(self, installation_id, account_login, html_url):
        data = {
            "installation_id": installation_id,
            "login": account_login,
            'html_url': html_url
        }
        self.client.table("installation_tokens").upsert(data).execute()
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
        self.client.table("installation_tokens").delete().eq("installation_id", installation_id).execute()
