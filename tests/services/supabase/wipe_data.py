import os
from services.supabase import SupabaseManager
from config import (
    OWNER_ID,
    USER_ID,
    INSTALLATION_ID,
)
from utils.timer import timer_decorator

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


@timer_decorator
def wipe_installation_owner_user_data(installation_id: int = INSTALLATION_ID) -> None:
    """Wipe all data from installations, owners, and users tables"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    supabase_manager.client.table("usage").delete().eq("user_id", USER_ID).eq(
        "installation_id", installation_id
    ).execute()

    supabase_manager.client.table("issues").delete().eq(
        "installation_id", installation_id
    ).execute()

    supabase_manager.client.table("installations").delete().eq(
        "installation_id", installation_id
    ).execute()

    data, _ = (
        supabase_manager.client.table("installations")
        .select("*")
        .eq("owner_id", OWNER_ID)
        .execute()
    )

    if len(data[1]) == 0:
        supabase_manager.client.table("owners").delete().eq(
            "owner_id", OWNER_ID
        ).execute()
