# Standard imports
import base64
import os

# Third-party imports
from dotenv import load_dotenv
load_dotenv()

# GitHub Credentials from environment variables
GITHUB_APP_ID = os.environ.get("APP_ID_GITHUB")
# GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
# GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
# GITHUB_INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")
GITHUB_PRIVATE_KEY_ENCODED = os.environ.get("GITHUB_PRIVATE_KEY")
GITHUB_PRIVATE_KEY = ''#base64.b64decode(GITHUB_PRIVATE_KEY_ENCODED)
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")

# Supabase Credentials from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET_KEY = os.environ.get("SUPABASE_JWT_SECRET_KEY")

# General
LABEL = "pragent"
