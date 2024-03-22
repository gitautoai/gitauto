from supabase import create_client, Client

from services.supabase.installation_token_manager import InstallationTokenManager
from services.supabase.users_manager import UsersManager


class SupabaseManager(InstallationTokenManager, UsersManager):
    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(supabase_url=url, supabase_key=key)
