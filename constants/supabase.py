from utils.env import get_env_var

SUPABASE_SERVICE_ROLE_KEY = get_env_var(name="SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = get_env_var(name="SUPABASE_URL")

# 1000 failed for delete_coverages_by_paths (URL too long), so set to 500
SUPABASE_BATCH_SIZE = 500
