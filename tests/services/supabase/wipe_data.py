import os
from config import (
    OWNER_ID,
    USER_ID,
    INSTALLATION_ID,
)
from services.supabase.client import supabase
from utils.timer import timer_decorator

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


@timer_decorator
def wipe_installation_owner_user_data(installation_id: int = INSTALLATION_ID) -> None:
    """Wipe all data from installations, owners, and users tables"""
    supabase.table("usage").delete().eq("user_id", USER_ID).eq(
        "installation_id", installation_id
    ).execute()

    supabase.table("issues").delete().eq("installation_id", installation_id).execute()

    supabase.table("installations").delete().eq(
        "installation_id", installation_id
    ).execute()

    data, _ = (
        supabase.table("installations").select("*").eq("owner_id", OWNER_ID).execute()
    )

    if len(data[1]) == 0:
        supabase.table("owners").delete().eq("owner_id", OWNER_ID).execute()
