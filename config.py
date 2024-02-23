# Standard imports
import base64
import os
import json

# Third-party imports
from dotenv import load_dotenv
load_dotenv()


# Function to get environment variable with error handling
def get_env_var(name: str) -> str:
    value: str | None = os.environ.get(name)
    if value is None:
        raise ValueError(f'Environment variable {name} not set.')
    return value


# GitHub Credentials from environment variables
GITHUB_APP_ID: str = get_env_var(name="GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_ENCODED: str = get_env_var(name="GITHUB_PRIVATE_KEY")
print(GITHUB_PRIVATE_KEY_ENCODED)
print(len(GITHUB_PRIVATE_KEY_ENCODED))
if(get_env_var("ENV") == "local"):
    GITHUB_PRIVATE_KEY_ENCODED = GITHUB_PRIVATE_KEY_ENCODED + '==\n-----END RSA PRIVATE KEY-----"}' 
    print(GITHUB_PRIVATE_KEY_ENCODED)
    print(len(GITHUB_PRIVATE_KEY_ENCODED))
GITHUB_PRIVATE_KEY_JSON = json.loads(GITHUB_PRIVATE_KEY_ENCODED, strict=False)
GITHUB_PRIVATE_KEY = GITHUB_PRIVATE_KEY_JSON['value']
print(GITHUB_PRIVATE_KEY_JSON)

GITHUB_WEBHOOK_SECRET: str = get_env_var(name="GITHUB_WEBHOOK_SECRET")


# Supabase Credentials from environment variables
SUPABASE_URL: str = get_env_var(name="SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: str = get_env_var(name="SUPABASE_SERVICE_ROLE_KEY")

# General
LABEL = "pragent"
