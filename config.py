import base64
import os

def get_env_var(name: str) -> str:
    value: str | None = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable {name} not set.")
    return value

# GitHub Credentials from environment variables
GITHUB_API_URL = "https://api.github.com"
GITHUB_APP_ID = int(get_env_var(name="GH_APP_ID"))
GITHUB_PRIVATE_KEY_ENCODED: str = get_env_var(name="GH_PRIVATE_KEY")
GITHUB_PRIVATE_KEY: bytes = base64.b64decode(s=GITHUB_PRIVATE_KEY_ENCODED)

# General
TIMEOUT = 120  # seconds

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "dummy_anthropic_api_key")

ANTHROPIC_MODEL_ID_40 = "claude-sonnet-4-0"
ANTHROPIC_MODEL_ID_40 = "claude-sonnet-4-0"
# Anthropic model IDs
ANTHROPIC_MODEL_ID_35 = "claude-3-5-sonnet-latest"
ANTHROPIC_MODEL_ID_40 = "claude-sonnet-4-0"

GITHUB_NOREPLY_EMAIL_DOMAIN = "noreply.github.com"
PRODUCT_ID_FOR_FREE = "prod_free_placeholder"
PRODUCT_ID_FOR_STANDARD = "prod_standard_placeholder"

TEST_INSTALLATION_ID = 12345
TEST_ISSUE_NUMBER = 1
TEST_NEW_INSTALLATION_ID = 67890
TEST_OWNER_ID = 1111
TEST_OWNER_NAME = "test_owner"
TEST_OWNER_TYPE = "organization"
TEST_REPO_ID = 2222
ANTHROPIC_MODEL_ID_40 = "claude-sonnet-4-0"
TEST_USER_ID = 3333
TEST_USER_NAME = "test_user"
TEST_EMAIL = "test@example.com"
TEST_REPO_NAME = "test_repo"
ANTHROPIC_MODEL_ID_40 = "claude-sonnet-4-0"
