from supabase import create_client, Client
import datetime


class InstallationTokenManager:
    def __init__(self, url, key):
        self.client: Client = create_client(url, key)

    def save_installation_token(self, installation_id, account_login, html_url, repositories, repository_ids):
        print("SAVING")
        try:
            data, _ = self.client.table("repo_info").select("*").eq("installation_id", installation_id).execute()
            if(len(data[1]) > 0):
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
        except Exception as e:
            print(e)
        print("DONE")
        
    def get_installation_id(self, repository_id):
        data, _ = self.client.table("repo_info").select("installation_id").contains('repository_ids', [str(repository_id)]).execute()
        if(data[1] and data[0][1]):
            return data[1][0].get('installation_id')
        raise RuntimeError("Installation ID for this repo not found.")


    def get_installation_token(self, installation_id):
        query = self.client.table("installation_tokens").select("access_token").eq("installation_id", installation_id)
        data = query.execute()
        if data.data and len(data.data) > 0:
            return data.data[0]['access_token']
 

    # Why this?
    def invalidate_installation_token(self, installation_id):
        data = {"access_token": ""}
        self.client.table("installation_tokens").update(data).eq("installation_id", installation_id).execute()

    def delete_installation_token(self, installation_id):
        data = {"deleted_at": datetime.datetime.utcnow().isoformat()}
        self.client.table("repo_info").update(data).eq("installation_id", installation_id).execute()
