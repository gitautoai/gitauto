import datetime
from supabase import create_client, Client


# Manager class to handle installation tokens
class InstallationTokenManager:
    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(supabase_url=url, supabase_key=key)

    def save_installation_token(self, installation_id, account_login: str, html_url: str, repositories, repository_ids) -> None:
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

    def get_installation_id(self, repository_id: int) -> str:
        data, _ = self.client.table(table_name="repo_info").select("installation_id").contains(column='repository_ids', value=[str(object=repository_id)]).execute()
        if (data[1] and data[0][1]):
            return data[1][0].get('installation_id')
        raise RuntimeError("Installation ID for this repo not found.")

    def delete_installation_token(self, installation_id: int) -> None:
        data: dict[str, str] = {"deleted_at": datetime.datetime.utcnow().isoformat()}
        self.client.table(table_name="repo_info").update(json=data).eq(column="installation_id", value=installation_id).execute()
