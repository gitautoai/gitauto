from supabase import create_client, Client
from constants.supabase import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL

# Initialize shared Supabase client
supabase: Client = create_client(
    supabase_url=SUPABASE_URL, supabase_key=SUPABASE_SERVICE_ROLE_KEY
)
