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
GITHUB_API_VERSION = "2022-11-28"
GITHUB_APP_ID = int(get_env_var(name="GH_APP_ID"))
GITHUB_APP_IDS = list(
    set(
        [
            GITHUB_APP_ID,  # Production or your local development
            844909,  # Production
            901480,  # Staging
        ]
    )
)
GITHUB_APP_NAME = get_env_var(name="GH_APP_NAME")
GITHUB_APP_USER_ID = int(get_env_var(name="GH_APP_USER_ID"))
GITHUB_APP_USER_NAME = get_env_var(name="GH_APP_USER_NAME")
GITHUB_CHECK_RUN_FAILURES = [
    "startup_failure",
    "failure",
    "timed_out",
]
GITHUB_ISSUE_DIR = ".github/ISSUE_TEMPLATE"
GITHUB_ISSUE_TEMPLATES = ["bug_report.yml", "feature_request.yml"]
GITHUB_NOREPLY_EMAIL_DOMAIN = "users.noreply.github.com"  # https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address
GITHUB_PRIVATE_KEY_ENCODED = get_env_var(name="GH_PRIVATE_KEY")
GITHUB_PRIVATE_KEY = base64.b64decode(s=GITHUB_PRIVATE_KEY_ENCODED)
GITHUB_WEBHOOK_SECRET = get_env_var(name="GH_WEBHOOK_SECRET")

# OpenAI Credentials from environment variables
OPENAI_API_KEY = get_env_var(name="OPENAI_API_KEY")
OPENAI_ASSISTANT_NAME = (
    "GitAuto: AI Coding Agent that generates GitHub pull requests from issues"
)
OPENAI_FINAL_STATUSES = ["cancelled", "completed", "expired", "failed"]
OPENAI_MAX_ARRAY_LENGTH = 32  # https://community.openai.com/t/assistant-threads-create-400-messages-array-too-long/754574/1
OPENAI_MAX_STRING_LENGTH = 1000000  # Secured 48576 as a buffer. https://gitauto-ai.sentry.io/issues/5582421505/?notification_uuid=016fc393-8f5d-45cf-8296-4ec6e264adcb&project=4506865231200256&referrer=regression_activity-slack and https://community.openai.com/t/assistant-threads-create-400-messages-array-too-long/754574/5
OPENAI_MAX_CONTEXT_TOKENS = 120000  # Secured 8,000 as a buffer. https://gitauto-ai.sentry.io/issues/5582421515/events/9a09416e714c4a66bf1bd86916702be2/?project=4506865231200256&referrer=issue_details.related_trace_issue
OPENAI_MAX_RETRIES = 3
OPENAI_MAX_TOOL_OUTPUTS_SIZE = 512 * 1024  # in bytes
OPENAI_MAX_TOKENS = 4096
OPENAI_MODEL_ID_GPT_5 = "gpt-5"  # https://platform.openai.com/docs/models
OPENAI_MODEL_ID_FOR_TIKTOKEN = (
    "gpt-4.1"  # https://github.com/openai/tiktoken/blob/main/tiktoken/model.py
)
OPENAI_ORG_ID = get_env_var(name="OPENAI_ORG_ID")
OPENAI_TEMPERATURE = 0.0

# Anthropic Credentials from environment variables
# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-aliases
ANTHROPIC_API_KEY = get_env_var(name="ANTHROPIC_API_KEY")
ANTHROPIC_MODEL_ID_35 = "claude-3-5-sonnet-latest"
ANTHROPIC_MODEL_ID_37 = "claude-3-7-sonnet-latest"
ANTHROPIC_MODEL_ID_40 = "claude-sonnet-4-0"

# Resend Credentials
RESEND_API_KEY = get_env_var(name="RESEND_API_KEY")
EMAIL_FROM = "Wes from GitAuto <wes@gitauto.ai>"

# Sentry Credentials from environment variables
SENTRY_DSN = get_env_var(name="SENTRY_DSN")

# Supabase Credentials from environment variables
SUPABASE_SERVICE_ROLE_KEY = get_env_var(name="SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = get_env_var(name="SUPABASE_URL")

# Stripe
STRIPE_API_KEY = get_env_var(name="STRIPE_API_KEY")
STRIPE_FREE_TIER_PRICE_ID = get_env_var(name="STRIPE_FREE_TIER_PRICE_ID")
STRIPE_PRODUCT_ID_FREE = get_env_var(name="STRIPE_PRODUCT_ID_FREE")
STRIPE_PRODUCT_ID_STANDARD = get_env_var(name="STRIPE_PRODUCT_ID_STANDARD")

# General
ONE_YEAR_FROM_NOW = datetime.now(timezone.utc).replace(
    year=datetime.now().year + 1, microsecond=0
)
EMAIL_LINK = "[info@gitauto.ai](mailto:info@gitauto.ai)"
ENV = get_env_var(name="ENV")
EXCEPTION_OWNERS = ["gitautoai", "Suchica", "hiroshinishio"]
# Update here too: https://dashboard.stripe.com/test/products/prod_PokLGIxiVUwCi6
CREDIT_AMOUNTS_USD = {
    "usage": -3,
    "grant": 10,
}
ISSUE_NUMBER_FORMAT = "/issue-"  # DO NOT USE "#" as it is a special character and has to be encoded in URL, like in GitHub API URL
MAX_RETRIES = 3
PER_PAGE = 100
PR_BODY_STARTS_WITH = "Resolves #"  # https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue
PRODUCT_ID = get_env_var(name="PRODUCT_ID")
PRODUCT_NAME = "GitAuto"
TIMEOUT = 120  # seconds
TZ = timezone.utc
UTF8 = "utf-8"

# Testing
TEST_APP_ID = 123456
TEST_INSTALLATION_ID = 12345678
TEST_NEW_INSTALLATION_ID = 87654321
PRODUCT_ID_FOR_STANDARD = "prod_PqZFpCs1Jq6X4E"  # https://dashboard.stripe.com/test/products/prod_PqZFpCs1Jq6X4E
TEST_OWNER_ID = 123456789
TEST_OWNER_TYPE = "Organization"
TEST_OWNER_NAME = "installation-test"
TEST_REPO_ID = 987654321
TEST_REPO_NAME = "test-repo"
TEST_ISSUE_NUMBER = 1234
TEST_USER_ID = 1234567
TEST_USER_NAME = "username-test"
TEST_EMAIL = "test@gitauto.ai"
