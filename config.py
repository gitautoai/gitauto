# Standard imports
import base64
import os

# Third-party imports
from dotenv import load_dotenv
load_dotenv()


# Function to get environment variable with error handling
def get_env_var(name: str) -> str:
    value = os.getenv(key=name)
    if value is None:
        raise ValueError(f"Environment variable {name} not set.")
    return value


# GitHub Credentials from environment variables
GITHUB_APP_ID = get_env_var(name="APP_ID_GITHUB")
GITHUB_PRIVATE_KEY_ENCODED = get_env_var(name="GITHUB_PRIVATE_KEY")
GITHUB_PRIVATE_KEY = base64.b64decode(s=GITHUB_PRIVATE_KEY_ENCODED)
GITHUB_WEBHOOK_SECRET = get_env_var(name="GITHUB_WEBHOOK_SECRET")

# Supabase Credentials from environment variables
SUPABASE_URL = get_env_var(name="SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = get_env_var(name="SUPABASE_SERVICE_ROLE_KEY")

# General
LABEL = "pragent"
