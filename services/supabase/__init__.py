from supabase import create_client, Client

from services.supabase.gitauto_manager import GitAutoAgentManager
from services.supabase.users_manager import UsersManager


class SupabaseManager(GitAutoAgentManager, UsersManager):
    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(supabase_url=url, supabase_key=key)
