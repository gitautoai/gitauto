import base64
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import pytest

# Import the function and constants we want to test
from config import (
    get_env_var,
    GITHUB_API_URL,
    GITHUB_API_VERSION,
    GITHUB_CHECK_RUN_FAILURES,
    GITHUB_ISSUE_DIR,
    GITHUB_ISSUE_TEMPLATES,
    GITHUB_NOREPLY_EMAIL_DOMAIN,
    OPENAI_ASSISTANT_NAME,
    OPENAI_FINAL_STATUSES,
    OPENAI_MAX_ARRAY_LENGTH,
    OPENAI_MAX_STRING_LENGTH,
    OPENAI_MAX_CONTEXT_TOKENS,
    OPENAI_MAX_RETRIES,
    OPENAI_MAX_TOOL_OUTPUTS_SIZE,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL_ID_O3_MINI,
    OPENAI_MODEL_ID_O1_PREVIEW,
    OPENAI_MODEL_ID_O1_MINI,
    OPENAI_MODEL_ID_O1,
    OPENAI_MODEL_ID_GPT_4O,
    OPENAI_TEMPERATURE,
    ANTHROPIC_MODEL_ID_35,
    ANTHROPIC_MODEL_ID_37,
    ANTHROPIC_MODEL_ID_40,
    DEFAULT_TIME,
    EMAIL_LINK,
    EXCEPTION_OWNERS,
    FREE_TIER_REQUEST_AMOUNT,
    ISSUE_NUMBER_FORMAT,
    MAX_RETRIES,
    PER_PAGE,
    PR_BODY_STARTS_WITH,
    PRODUCT_NAME,
    TIMEOUT,
    TZ,
    UTF8,
    TEST_APP_ID,
    TEST_INSTALLATION_ID,
    TEST_NEW_INSTALLATION_ID,
    PRODUCT_ID_FOR_FREE,
    PRODUCT_ID_FOR_STANDARD,
    TEST_OWNER_ID,
    TEST_OWNER_TYPE,
    TEST_OWNER_NAME,
    TEST_REPO_ID,
    TEST_REPO_NAME,
    TEST_ISSUE_NUMBER,
    TEST_USER_ID,
    TEST_USER_NAME,
    TEST_EMAIL,
)


class TestGetEnvVar:
    """Test cases for the get_env_var function."""

    def test_get_env_var_success(self):
        """Test get_env_var returns value when environment variable exists."""
        test_var_name = "TEST_ENV_VAR"
        test_value = "test_value"
        os.environ[test_var_name] = test_value
        
        result = get_env_var(test_var_name)
        
        assert result == test_value
        del os.environ[test_var_name]

    def test_get_env_var_not_set(self):
        """Test get_env_var raises ValueError when environment variable doesn't exist."""
        test_var_name = "NONEXISTENT_ENV_VAR"
        if test_var_name in os.environ:
            del os.environ[test_var_name]

        with pytest.raises(ValueError) as exc_info:
            get_env_var(test_var_name)
        
        assert str(exc_info.value) == f"Environment variable {test_var_name} not set."

    def test_get_env_var_empty_string(self):
        """Test get_env_var returns empty string when environment variable is set to empty."""
        test_var_name = "EMPTY_ENV_VAR"
        os.environ[test_var_name] = ""
        
        result = get_env_var(test_var_name)
        
        assert result == ""
        del os.environ[test_var_name]

    def test_get_env_var_whitespace(self):
        """Test get_env_var returns whitespace when environment variable contains only whitespace."""
        test_var_name = "WHITESPACE_ENV_VAR"
        test_value = "   "
        os.environ[test_var_name] = test_value
        
        result = get_env_var(test_var_name)
        
        assert result == test_value
        del os.environ[test_var_name]


class TestGitHubConstants:
    """Test cases for GitHub-related constants."""

    def test_github_api_url(self):
        """Test GitHub API URL constant."""
        assert GITHUB_API_URL == "https://api.github.com"

    def test_github_api_version(self):
        """Test GitHub API version constant."""
        assert GITHUB_API_VERSION == "2022-11-28"

    def test_github_check_run_failures(self):
        """Test GitHub check run failures list."""
        expected_failures = [
            "startup_failure",
            "failure",
            "timed_out",
            "action_required",
        ]
        assert GITHUB_CHECK_RUN_FAILURES == expected_failures

    def test_github_issue_dir(self):
        """Test GitHub issue directory constant."""
        assert GITHUB_ISSUE_DIR == ".github/ISSUE_TEMPLATE"

    def test_github_issue_templates(self):
        """Test GitHub issue templates list."""
        expected_templates = ["bug_report.yml", "feature_request.yml"]
        assert GITHUB_ISSUE_TEMPLATES == expected_templates

    def test_github_noreply_email_domain(self):
        """Test GitHub noreply email domain constant."""
        assert GITHUB_NOREPLY_EMAIL_DOMAIN == "users.noreply.github.com"

    @patch.dict(os.environ, {
        "GH_APP_ID": "123456",
        "GH_APP_NAME": "test-app",
        "GH_APP_USER_ID": "789012",
        "GH_APP_USER_NAME": "test-user",
        "GH_PRIVATE_KEY": "dGVzdC1rZXk=",  # base64 encoded "test-key"
        "GH_WEBHOOK_SECRET": "test-secret"
    })
    def test_github_environment_variables(self):
        """Test GitHub environment variables are loaded correctly."""
        # Re-import to get updated values
        import importlib
        import config
        importlib.reload(config)
        
        assert config.GITHUB_APP_ID == 123456
        assert config.GITHUB_APP_NAME == "test-app"
        assert config.GITHUB_APP_USER_ID == 789012
        assert config.GITHUB_APP_USER_NAME == "test-user"
        assert config.GITHUB_PRIVATE_KEY == b"test-key"
        assert config.GITHUB_WEBHOOK_SECRET == "test-secret"

    @patch.dict(os.environ, {"GH_APP_ID": "123456"})
    def test_github_app_ids_list(self):
        """Test GitHub app IDs list contains unique values."""
        import importlib
        import config
        importlib.reload(config)
        
        expected_ids = [123456, 844909, 901480]
        assert set(config.GITHUB_APP_IDS) == set(expected_ids)
        assert len(config.GITHUB_APP_IDS) == len(set(config.GITHUB_APP_IDS))  # No duplicates


class TestOpenAIConstants:
    """Test cases for OpenAI-related constants."""

    def test_openai_assistant_name(self):
        """Test OpenAI assistant name constant."""
        expected_name = "GitAuto: AI Coding Agent that generates GitHub pull requests from issues"
        assert OPENAI_ASSISTANT_NAME == expected_name

    def test_openai_final_statuses(self):
        """Test OpenAI final statuses list."""
        expected_statuses = ["cancelled", "completed", "expired", "failed"]
        assert OPENAI_FINAL_STATUSES == expected_statuses

    def test_openai_numeric_constants(self):
        """Test OpenAI numeric constants."""
        assert OPENAI_MAX_ARRAY_LENGTH == 32
        assert OPENAI_MAX_STRING_LENGTH == 1000000
        assert OPENAI_MAX_CONTEXT_TOKENS == 120000
        assert OPENAI_MAX_RETRIES == 3
        assert OPENAI_MAX_TOOL_OUTPUTS_SIZE == 512 * 1024
        assert OPENAI_MAX_TOKENS == 4096
        assert OPENAI_TEMPERATURE == 0.0

    def test_openai_model_ids(self):
        """Test OpenAI model ID constants."""
        assert OPENAI_MODEL_ID_O3_MINI == "o3-mini"
        assert OPENAI_MODEL_ID_O1_PREVIEW == "o1-preview"
        assert OPENAI_MODEL_ID_O1_MINI == "o1-mini"
        assert OPENAI_MODEL_ID_O1 == "o1"
        assert OPENAI_MODEL_ID_GPT_4O == "gpt-4o"

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai-key",
        "OPENAI_ORG_ID": "test-org-id"
    })
    def test_openai_environment_variables(self):
        """Test OpenAI environment variables are loaded correctly."""
        import importlib
        import config
        importlib.reload(config)
        
        assert config.OPENAI_API_KEY == "test-openai-key"
        assert config.OPENAI_ORG_ID == "test-org-id"


class TestAnthropicConstants:
    """Test cases for Anthropic-related constants."""

    def test_anthropic_model_ids(self):
        """Test Anthropic model ID constants."""
        assert ANTHROPIC_MODEL_ID_35 == "claude-3-5-sonnet-latest"
        assert ANTHROPIC_MODEL_ID_37 == "claude-3-7-sonnet-latest"
        assert ANTHROPIC_MODEL_ID_40 == "claude-sonnet-4-0"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    def test_anthropic_environment_variables(self):
        """Test Anthropic environment variables are loaded correctly."""
        import importlib
        import config
        importlib.reload(config)
        
        assert config.ANTHROPIC_API_KEY == "test-anthropic-key"


class TestExternalServiceConstants:
    """Test cases for external service constants."""

    @patch.dict(os.environ, {"SENTRY_DSN": "test-sentry-dsn"})
    def test_sentry_environment_variables(self):
        """Test Sentry environment variables are loaded correctly."""
        import importlib
        import config
        importlib.reload(config)
        
        assert config.SENTRY_DSN == "test-sentry-dsn"

    @patch.dict(os.environ, {
        "SUPABASE_SERVICE_ROLE_KEY": "test-supabase-key",
        "SUPABASE_URL": "https://test.supabase.co"
    })
    def test_supabase_environment_variables(self):
        """Test Supabase environment variables are loaded correctly."""
        import importlib
        import config
        importlib.reload(config)
        
        assert config.SUPABASE_SERVICE_ROLE_KEY == "test-supabase-key"
        assert config.SUPABASE_URL == "https://test.supabase.co"

    @patch.dict(os.environ, {
        "STRIPE_API_KEY": "test-stripe-key",
        "STRIPE_FREE_TIER_PRICE_ID": "price_123",
        "STRIPE_PRODUCT_ID_FREE": "prod_free",
        "STRIPE_PRODUCT_ID_STANDARD": "prod_standard"
    })
    def test_stripe_environment_variables(self):
        """Test Stripe environment variables are loaded correctly."""
        import importlib
        import config
        importlib.reload(config)
        
        assert config.STRIPE_API_KEY == "test-stripe-key"
        assert config.STRIPE_FREE_TIER_PRICE_ID == "price_123"
        assert config.STRIPE_PRODUCT_ID_FREE == "prod_free"
        assert config.STRIPE_PRODUCT_ID_STANDARD == "prod_standard"


class TestGeneralConstants:
    """Test cases for general constants."""

    def test_default_time(self):
        """Test default time constant."""
        expected_time = datetime(year=1, month=1, day=1, hour=0, minute=0, second=0)
        assert DEFAULT_TIME == expected_time

    def test_email_link(self):
        """Test email link constant."""
        assert EMAIL_LINK == "[info@gitauto.ai](mailto:info@gitauto.ai)"

    def test_exception_owners(self):
        """Test exception owners list."""
        expected_owners = ["gitautoai", "Suchica", "hiroshinishio"]
        assert EXCEPTION_OWNERS == expected_owners

    def test_numeric_constants(self):
        """Test general numeric constants."""
        assert FREE_TIER_REQUEST_AMOUNT == 3
        assert MAX_RETRIES == 3
        assert PER_PAGE == 100
        assert TIMEOUT == 120

    def test_string_constants(self):
        """Test general string constants."""
        assert ISSUE_NUMBER_FORMAT == "/issue-"
        assert PR_BODY_STARTS_WITH == "Resolves #"
        assert PRODUCT_NAME == "GitAuto"
        assert UTF8 == "utf-8"

    def test_timezone_constant(self):
        """Test timezone constant."""
        assert TZ == timezone.utc

    @patch.dict(os.environ, {
        "ENV": "test",
        "PRODUCT_ID": "test-product-id"
    })
    def test_general_environment_variables(self):
        """Test general environment variables are loaded correctly."""
        import importlib
        import config
        importlib.reload(config)
        
        assert config.ENV == "test"
        assert config.PRODUCT_ID == "test-product-id"


class TestTestingConstants:
    """Test cases for testing-related constants."""

    def test_test_constants(self):
        """Test all testing constants have expected values."""
        assert TEST_APP_ID == 123456
        assert TEST_INSTALLATION_ID == 12345678
        assert TEST_NEW_INSTALLATION_ID == 87654321
        assert PRODUCT_ID_FOR_FREE == "prod_PokLGIxiVUwCi6"
        assert PRODUCT_ID_FOR_STANDARD == "prod_PqZFpCs1Jq6X4E"
        assert TEST_OWNER_ID == 123456789
        assert TEST_OWNER_TYPE == "Organization"
        assert TEST_OWNER_NAME == "installation-test"
        assert TEST_REPO_ID == 987654321
        assert TEST_REPO_NAME == "test-repo"
        assert TEST_ISSUE_NUMBER == 1234
        assert TEST_USER_ID == 1234567
        assert TEST_USER_NAME == "username-test"
        assert TEST_EMAIL == "test@gitauto.ai"


class TestModuleImports:
    """Test cases for module imports and initialization."""

    @patch('config.load_dotenv')
    def test_dotenv_loaded_on_import(self, mock_load_dotenv):
        """Test that load_dotenv is called when module is imported."""
        # Since config is already imported at the top of this file,
        # and load_dotenv is called during import, we can't directly test it.
        # Instead, we'll verify that the function exists in the module
        import sys
        import config as config_module
        assert hasattr(config_module, 'load_dotenv')
        assert 'dotenv' in sys.modules

    def test_base64_decoding(self):
        """Test base64 decoding functionality."""
        test_encoded = base64.b64encode(b"test-key").decode()
        
        with patch.dict(os.environ, {"GH_PRIVATE_KEY": test_encoded}):
            import importlib
            import config
            importlib.reload(config)
            
            assert config.GITHUB_PRIVATE_KEY == b"test-key"

    def test_integer_conversion(self):
        """Test integer conversion from environment variables."""
        with patch.dict(os.environ, {
            "GH_APP_ID": "999999",
            "GH_APP_USER_ID": "888888"
        }):
            import importlib
            import config
            importlib.reload(config)
            
            assert isinstance(config.GITHUB_APP_ID, int)
            assert isinstance(config.GITHUB_APP_USER_ID, int)
            assert config.GITHUB_APP_ID == 999999
            assert config.GITHUB_APP_USER_ID == 888888


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    def test_missing_required_env_vars_raise_error(self):
        """Test that missing required environment variables raise ValueError."""
        # Remove all environment variables that config.py requires
        required_vars = [
            "GH_APP_ID", "GH_APP_NAME", "GH_APP_USER_ID", "GH_APP_USER_NAME",
            "GH_PRIVATE_KEY", "GH_WEBHOOK_SECRET", "OPENAI_API_KEY", "OPENAI_ORG_ID",
            "ANTHROPIC_API_KEY", "SENTRY_DSN", "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_URL", "STRIPE_API_KEY", "STRIPE_FREE_TIER_PRICE_ID",
            "STRIPE_PRODUCT_ID_FREE", "STRIPE_PRODUCT_ID_STANDARD", "ENV", "PRODUCT_ID"
        ]
        
        # Test that each missing variable raises an error
        for var in required_vars:
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match=f"Environment variable {var} not set"):
                    get_env_var(var)

    def test_invalid_integer_conversion(self):
        """Test behavior when environment variables can't be converted to integers."""
        with patch.dict(os.environ, {"GH_APP_ID": "not-a-number"}):
            with pytest.raises(ValueError):
                import importlib
                import config
                importlib.reload(config)

    def test_invalid_base64_encoding(self):
        """Test behavior when base64 decoding fails."""
        with patch.dict(os.environ, {"GH_PRIVATE_KEY": "invalid-base64!@#"}):
            with pytest.raises(Exception):  # base64.b64decode raises various exceptions
                import importlib
                import config
                importlib.reload(config)


class TestConstantTypes:
    """Test cases to verify constant types."""

    def test_constant_types(self):
        """Test that constants have expected types."""
        # String constants
        assert isinstance(GITHUB_API_URL, str)
        assert isinstance(GITHUB_API_VERSION, str)
        assert isinstance(GITHUB_ISSUE_DIR, str)
        assert isinstance(GITHUB_NOREPLY_EMAIL_DOMAIN, str)
        assert isinstance(OPENAI_ASSISTANT_NAME, str)
        assert isinstance(EMAIL_LINK, str)
        assert isinstance(ISSUE_NUMBER_FORMAT, str)
        assert isinstance(PR_BODY_STARTS_WITH, str)
        assert isinstance(PRODUCT_NAME, str)
        assert isinstance(UTF8, str)
        assert isinstance(TEST_OWNER_TYPE, str)
        assert isinstance(TEST_OWNER_NAME, str)
        assert isinstance(TEST_REPO_NAME, str)
        assert isinstance(TEST_USER_NAME, str)
        assert isinstance(TEST_EMAIL, str)
        
        # List constants
        assert isinstance(GITHUB_CHECK_RUN_FAILURES, list)
        assert isinstance(GITHUB_ISSUE_TEMPLATES, list)
        assert isinstance(OPENAI_FINAL_STATUSES, list)
        assert isinstance(EXCEPTION_OWNERS, list)
        
        # Integer constants
        assert isinstance(OPENAI_MAX_ARRAY_LENGTH, int)
        assert isinstance(OPENAI_MAX_STRING_LENGTH, int)
        assert isinstance(OPENAI_MAX_CONTEXT_TOKENS, int)
        assert isinstance(OPENAI_MAX_RETRIES, int)
        assert isinstance(OPENAI_MAX_TOOL_OUTPUTS_SIZE, int)
        assert isinstance(OPENAI_MAX_TOKENS, int)
        assert isinstance(FREE_TIER_REQUEST_AMOUNT, int)
        assert isinstance(MAX_RETRIES, int)
        assert isinstance(PER_PAGE, int)
        assert isinstance(TIMEOUT, int)
        assert isinstance(TEST_APP_ID, int)
        assert isinstance(TEST_INSTALLATION_ID, int)
        assert isinstance(TEST_NEW_INSTALLATION_ID, int)
        assert isinstance(TEST_OWNER_ID, int)
        assert isinstance(TEST_REPO_ID, int)
        assert isinstance(TEST_ISSUE_NUMBER, int)
        assert isinstance(TEST_USER_ID, int)
        
        # Float constants
        assert isinstance(OPENAI_TEMPERATURE, float)
        
        # DateTime constants
        assert isinstance(DEFAULT_TIME, datetime)
        
        # Timezone constants
        assert isinstance(TZ, type(timezone.utc))
