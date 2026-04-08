# Standard imports
import base64
from datetime import timezone
import os

# Third-party imports
from dotenv import load_dotenv

load_dotenv()


# GitHub Credentials from environment variables
GITHUB_API_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
GITHUB_APP_ID = int(os.getenv("GH_APP_ID", "0"))
GITHUB_APP_IDS = list(
    set(
        [
            GITHUB_APP_ID,  # Production or your local development
            844909,  # Production
            901480,  # Staging
        ]
    )
)
GITHUB_APP_NAME = os.getenv("GH_APP_NAME", "")
GITHUB_APP_USER_ID = int(os.getenv("GH_APP_USER_ID", "0"))
GITHUB_APP_USER_NAME = os.getenv("GH_APP_USER_NAME", "")
GITHUB_CHECK_RUN_FAILURES = [
    "startup_failure",
    "failure",
    "timed_out",
]
GITHUB_NOREPLY_EMAIL_DOMAIN = "users.noreply.github.com"  # https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address
# GitAuto's noreply email for git commits
GITHUB_APP_GIT_EMAIL = (
    f"{GITHUB_APP_USER_ID}+{GITHUB_APP_USER_NAME}@{GITHUB_NOREPLY_EMAIL_DOMAIN}"
)
GITHUB_PRIVATE_KEY_ENCODED = os.getenv("GH_PRIVATE_KEY", "")
GITHUB_PRIVATE_KEY = (
    base64.b64decode(s=GITHUB_PRIVATE_KEY_ENCODED)
    if GITHUB_PRIVATE_KEY_ENCODED
    else b""
)
GITHUB_WEBHOOK_SECRET = os.getenv("GH_WEBHOOK_SECRET", "")

# OpenAI Credentials from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
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
OPENAI_MODEL_ID = "gpt-5.2"  # https://platform.openai.com/docs/models/gpt-5.2
OPENAI_MODEL_ID_FOR_TIKTOKEN = (
    "gpt-4.1"  # https://github.com/openai/tiktoken/blob/main/tiktoken/model.py
)
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
OPENAI_TEMPERATURE = 0.0

# Resend Credentials
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = "Wes from GitAuto <wes@gitauto.ai>"

# Sentry Credentials from environment variables
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Stripe
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")

# General
EMAIL_LINK = "[info@gitauto.ai](mailto:info@gitauto.ai)"
ENV = os.getenv("ENV", "")
EXCEPTION_OWNERS = ["gitautoai", "Suchica", "hiroshinishio"]
# Update here too: https://dashboard.stripe.com/test/products/prod_PokLGIxiVUwCi6
CREDIT_USAGE_USD = 8
CREDIT_AMOUNTS_USD = {
    "usage": -CREDIT_USAGE_USD,
    "grant": CREDIT_USAGE_USD * 3,
}
MAX_RETRIES = 3
PER_PAGE = 100
PRODUCT_ID = os.getenv("PRODUCT_ID", "")
TIMEOUT = 120  # seconds
TZ = timezone.utc
UTF8 = "utf-8"

# Testing
TEST_APP_ID = 123456
TEST_INSTALLATION_ID = 12345678
TEST_NEW_INSTALLATION_ID = 87654321
TEST_OWNER_ID = 123456789
TEST_OWNER_TYPE = "Organization"
TEST_OWNER_NAME = "installation-test"
TEST_REPO_ID = 987654321
TEST_REPO_NAME = "test-repo"
TEST_ISSUE_NUMBER = 1234
TEST_USER_ID = 1234567
TEST_USER_NAME = "username-test"
TEST_EMAIL = "test@gitauto.ai"
