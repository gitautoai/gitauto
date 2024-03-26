# Standard imports
import base64
import os

# Third-party imports
from dotenv import load_dotenv

load_dotenv()


def get_env_var(name: str) -> str:
    value: str | None = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable {name} not set.")
    return value


# GitHub Credentials from environment variables
GITHUB_API_URL: str = "https://api.github.com"
GITHUB_API_VERSION: str = "2022-11-28"
GITHUB_APP_ID: str = get_env_var(name="GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_ENCODED: str = get_env_var(name="GITHUB_PRIVATE_KEY")
GITHUB_PRIVATE_KEY: bytes = base64.b64decode(s=GITHUB_PRIVATE_KEY_ENCODED)
GITHUB_WEBHOOK_SECRET: str = get_env_var(name="GITHUB_WEBHOOK_SECRET")

# OpenAI Credentials from environment variables
OPENAI_API_KEY: str = get_env_var(name="OPENAI_API_KEY")
OPENAI_FINAL_STATUSES: list[str] = ["cancelled", "completed", "expired", "failed"]
OPENAI_MAX_TOKENS = 4096
OPENAI_MODEL_ID = "gpt-4-turbo-preview"
OPENAI_ORG_ID: str = get_env_var(name="OPENAI_ORG_ID")
OPENAI_TEMPERATURE = 0.0

# Supabase Credentials from environment variables
SUPABASE_SERVICE_ROLE_KEY: str = get_env_var(name="SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL: str = get_env_var(name="SUPABASE_URL")

# Stripe
STRIPE_API_KEY: str = get_env_var(name="STRIPE_API_KEY")

# General
ENV: str = get_env_var(name="ENV")
PRODUCT_ID: str = get_env_var(name="PRODUCT_ID")
PRODUCT_NAME = "GitAuto"
TIMEOUT_IN_SECONDS = 120

ISSUE_NUMBER_FORMAT = "/issue-#"
PR_BODY_STARTS_WITH = "Original issue: [#"
