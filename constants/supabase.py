import os

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")

# 500 caused "URI Too Long" for .in_() with long file paths in delete_coverages_by_paths
SUPABASE_BATCH_SIZE = 100
