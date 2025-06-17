import os
from config import TEST_OWNER_ID, TEST_USER_ID, TEST_INSTALLATION_ID, TEST_USER_NAME
from services.supabase.client import supabase
from utils.time.timer import timer_decorator

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

@timer_decorator

def wipe_installation_owner_user_data(installation_id: int = TEST_INSTALLATION_ID) -> None:
    """Wipe all data from installations, owners, and users tables"""
    # Delete usage records first (foreign key constraint)
    supabase.table("usage")
        .delete()
        .eq("user_id", TEST_USER_ID)
        .eq("installation_id", installation_id)
        .execute()
    
    # Delete repositories records (foreign key constraint)
    supabase.table("repositories")
        .delete()
        .eq("owner_id", TEST_OWNER_ID)
        .execute()
    
    # Delete coverages records (foreign key constraint)
    supabase.table("coverages")
        .delete()
        .eq("installation_id", installation_id)
        .execute()
    
    # Delete pull_requests records (foreign key constraint)
    supabase.table("pull_requests")
        .delete()
        .eq("installation_id", installation_id)
        .execute()
    
    # Delete issues
    supabase.table("issues")
        .delete()
        .eq("installation_id", installation_id)
        .execute()
    
    # Delete installations
    supabase.table("installations")
        .delete()
        .eq("installation_id", installation_id)
        .execute()
    
    # Delete user
    supabase.table("users")
        .delete()
        .eq("user_id", TEST_USER_ID)
        .execute()
    supabase.table("users")
        .delete()
        .eq("user_name", TEST_USER_NAME)
        .execute()
    
    # Check if owner has any other installations
    data, _ = supabase.table("installations")
        .select("*")
        .eq("owner_id", TEST_OWNER_ID)
        .execute()
    
    # If no other installations exist, delete owner
    if len(data[1]) == 0:
        supabase.table("owners")
            .delete()
            .eq("owner_id", TEST_OWNER_ID)
            .execute()
