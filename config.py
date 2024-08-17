# Standard imports
import base64
import os
from datetime import datetime, timezone

# Third-party imports
from dotenv import load_dotenv

load_dotenv()


def get_env_var(name: str) -> str:
    value: str | None = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable {name} not set.")
    return value


# GitHub Credentials from environment variables
GITHUB_API_URL = "https://api.github.com"
GITHUB_API_VERSION: str = "2022-11-28"
GITHUB_APP_ID = int(get_env_var(name="GH_APP_ID"))
GITHUB_APP_IDS: list[int] = list(
    set(
        [
            GITHUB_APP_ID,  # Production or your local development
            844909,  # Production
            901480,  # Staging
        ]
    )
)
GITHUB_APP_NAME: str = get_env_var(name="GH_APP_NAME")
GITHUB_APP_USER_ID: int = int(get_env_var(name="GH_APP_USER_ID"))
GITHUB_APP_USER_NAME: str = get_env_var(name="GH_APP_USER_NAME")
GITHUB_ISSUE_DIR = ".github/ISSUE_TEMPLATE"
GITHUB_ISSUE_TEMPLATES: list[str] = ["bug_report.yml", "feature_request.yml"]
GITHUB_PRIVATE_KEY_ENCODED: str = get_env_var(name="GH_PRIVATE_KEY")
GITHUB_PRIVATE_KEY: bytes = base64.b64decode(s=GITHUB_PRIVATE_KEY_ENCODED)
GITHUB_WEBHOOK_SECRET: str = get_env_var(name="GH_WEBHOOK_SECRET")

# OpenAI Credentials from environment variables
OPENAI_API_KEY: str = get_env_var(name="OPENAI_API_KEY")
OPENAI_ASSISTANT_NAME = (
    "GitAuto: AI Coding Agent that generates GitHub pull requests from issues"
)
OPENAI_FINAL_STATUSES = ["cancelled", "completed", "expired", "failed"]
OPENAI_MAX_ARRAY_LENGTH = 32  # https://community.openai.com/t/assistant-threads-create-400-messages-array-too-long/754574/1
OPENAI_MAX_STRING_LENGTH = 256000  # https://community.openai.com/t/assistant-threads-create-400-messages-array-too-long/754574/5
OPENAI_MAX_CONTEXT_TOKENS = 128000  # https://gitauto-ai.sentry.io/issues/5582421515/events/9a09416e714c4a66bf1bd86916702be2/?project=4506865231200256&referrer=issue_details.related_trace_issue
OPENAI_MAX_RETRIES = 3
OPENAI_MAX_TOOL_OUTPUTS_SIZE = 512 * 1024  # in bytes
OPENAI_MAX_TOKENS = 4096
OPENAI_MODEL_ID = "gpt-4o-2024-08-06"
OPENAI_ORG_ID: str = get_env_var(name="OPENAI_ORG_ID")
OPENAI_TEMPERATURE = 0.0

# Supabase Credentials from environment variables
SUPABASE_SERVICE_ROLE_KEY: str = get_env_var(name="SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL: str = get_env_var(name="SUPABASE_URL")

# Stripe
STRIPE_API_KEY: str = get_env_var(name="STRIPE_API_KEY")
STRIPE_FREE_TIER_PRICE_ID: str = get_env_var(name="STRIPE_FREE_TIER_PRICE_ID")

# General
DEFAULT_TIME = datetime(year=1, month=1, day=1, hour=0, minute=0, second=0)
EMAIL_LINK = "[info@gitauto.ai](mailto:info@gitauto.ai)"
ENV: str = get_env_var(name="ENV")
IS_PRD: bool = ENV == "prod"
# Update here too: https://dashboard.stripe.com/test/products/prod_PokLGIxiVUwCi6
FREE_TIER_REQUEST_AMOUNT = 5
ISSUE_NUMBER_FORMAT = "/issue-#"
MAX_RETRIES = 3
PER_PAGE = 100
PR_BODY_STARTS_WITH = "Original issue: [#"
PRODUCT_ID: str = get_env_var(name="PRODUCT_ID")
PRODUCT_NAME = "GitAuto"
PRODUCT_URL = "https://gitauto.ai"
TIMEOUT = 120  # seconds
TZ = timezone.utc
UTF8 = "utf-8"

# Testing
INSTALLATION_ID = -1
NEW_INSTALLATION_ID = -2
PRODUCT_ID_FOR_FREE = "prod_PokLGIxiVUwCi6"  # https://dashboard.stripe.com/test/products/prod_PokLGIxiVUwCi6
PRODUCT_ID_FOR_STANDARD = "prod_PqZFpCs1Jq6X4E"  # https://dashboard.stripe.com/test/products/prod_PqZFpCs1Jq6X4E
OWNER_ID = -1
OWNER_NAME = "installation-test"
EXCEPTION_OWNERS = ["gitautoai", "hiroshinishio"]
OWNER_TYPE = "Organization"
UNIQUE_ISSUE_ID = "O/gitautoai/test#1"
USER_ID = -1
USER_NAME = "username-test"
