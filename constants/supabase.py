from utils.env import get_env_var

SUPABASE_SERVICE_ROLE_KEY = get_env_var(name="SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = get_env_var(name="SUPABASE_URL")

# 500 caused "URI Too Long" for .in_() with long file paths in delete_coverages_by_paths
SUPABASE_BATCH_SIZE = 100
