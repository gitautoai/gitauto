# Standard imports
import base64
import os

# Third-party imports
from dotenv import load_dotenv
load_dotenv()

# GitHub Credentials from environment variables
GITHUB_APP_ID = os.getenv(key="APP_ID_GITHUB")
GITHUB_PRIVATE_KEY_ENCODED = os.getenv(key="GITHUB_PRIVATE_KEY")
if GITHUB_PRIVATE_KEY_ENCODED is None:
    raise ValueError("GitHub private key not provided.")
try:
    GITHUB_PRIVATE_KEY = base64.b64decode(s=GITHUB_PRIVATE_KEY_ENCODED)
except Exception as e:
    raise ValueError(f"GitHub private key could not be decoded: {e}")
GITHUB_WEBHOOK_SECRET = os.getenv(key="GITHUB_WEBHOOK_SECRET")

# Supabase Credentials from environment variables
SUPABASE_URL = os.getenv(key="SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(key="SUPABASE_SERVICE_ROLE_KEY")

# General
LABEL = "pragent"
