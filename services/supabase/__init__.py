from supabase import create_client, Client

from .gitauto_manager import GitAutoAgentManager
from .users_manager import UsersManager


class SupabaseManager(GitAutoAgentManager, UsersManager):
    "Combines all supabase services into one manager so you only need to instntiate one object."

    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(supabase_url=url, supabase_key=key)
