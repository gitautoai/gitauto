import datetime
from supabase import create_client, Client
import logging

# Manager class to handle installation tokens
class InstallationTokenManager:
    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(supabase_url=url, supabase_key=key)

    def save_installation_token(
            self, installation_id: int, account_login: str, html_url: str,
            repositories: list[str], repository_ids: list[int]) -> None:
        data, _ = self.client.table(table_name="repo_info").select("*").eq(column="installation_id", value=installation_id).execute()
        if (len(data[1]) > 0):
            self.client.table(table_name="repo_info").update(json={
                "installation_id": installation_id,
                "login": account_login,
                'html_url': html_url,
                "repositories": repositories,
                "repository_ids": repository_ids,
                "deleted_at": None,
            }).eq(column="installation_id", value=installation_id).execute()
        else:
            self.client.table(table_name="repo_info").insert(json={
                "installation_id": installation_id,
                "login": account_login,
                'html_url': html_url,
                "repositories": repositories,
                "repository_ids": repository_ids,
            }).execute()


    def delete_installation_token(self, installation_id: int) -> None:
        data: dict[str, str] = {"deleted_at": datetime.datetime.utcnow().isoformat()}
        self.client.table(table_name="repo_info").update(json=data).eq(column="installation_id", value=installation_id).execute()
        
    def increment_request_count(self, installation_id: int) -> None:
        try: 
            data, _ = self.client.table(table_name="repo_info").select("*").eq(column="installation_id", value=installation_id).execute()
            if (data[1] and data[1][0]):
                self.client.table(table_name="repo_info").update(json={"requests": data[1][0]['requests'] + 1}).eq(column="installation_id", value=installation_id).execute()
        except Exception as e:
            logging.error(msg=f"Increment Request Count Error: {e}")