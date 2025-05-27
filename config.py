import os
from datetime import datetime, timezone

# General constants
DEFAULT_TIME = datetime(year=1, month=1, day=1, hour=0, minute=0, second=0)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "dummy_anthropic_api_key")

# Anthropic model IDs
ANTHROPIC_MODEL_ID_35 = "claude-3-5-sonnet-latest"
ANTHROPIC_MODEL_ID_40 = "claude-sonnet-4-0"

GITHUB_NOREPLY_EMAIL_DOMAIN = "noreply.github.com"
PRODUCT_ID_FOR_FREE = "prod_free_placeholder"
PRODUCT_ID_FOR_STANDARD = "prod_standard_placeholder"

# Stripe constants
STRIPE_FREE_TIER_PRICE_ID = os.environ.get("STRIPE_FREE_TIER_PRICE_ID", "price_free_placeholder")

# Timezone
TZ = timezone.utc

TEST_INSTALLATION_ID = 12345
TEST_ISSUE_NUMBER = 1
TEST_NEW_INSTALLATION_ID = 67890
TEST_OWNER_ID = 1111
TEST_OWNER_NAME = "test_owner"
TEST_OWNER_TYPE = "organization"
TEST_REPO_ID = 2222
TEST_USER_ID = 3333
TEST_USER_NAME = "test_user"
TEST_EMAIL = "test@example.com"
TEST_REPO_NAME = "test_repo"