"""
Separate test file for testing Sentry initialization in production environment.
This file must be run separately to ensure ENV is set before main.py is imported.
"""

# Standard imports
import os
import sys
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest


class TestSentryInitializationInProd:
    """Test Sentry initialization when ENV is set to 'prod'."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Remove main module if already imported
        if "main" in sys.modules:
            del sys.modules["main"]
        yield
        # Cleanup after test
        if "main" in sys.modules:
            del sys.modules["main"]

    @patch.dict(os.environ, {"ENV": "prod"})
    @patch("sentry_sdk.init")
    def test_sentry_init_called_when_env_is_prod(self, mock_sentry_init):
        """Test that sentry_sdk.init is called when ENV is 'prod'."""
        # Import main module with ENV set to prod
        import main  # pylint: disable=import-outside-toplevel,unused-import

        # Verify Sentry was initialized
        mock_sentry_init.assert_called_once()

        # Verify the call arguments
        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["environment"] == "prod"
        assert call_kwargs["traces_sample_rate"] == 1.0
