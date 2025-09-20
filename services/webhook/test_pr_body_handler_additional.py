"""Additional unit tests for pr_body_handler.py to improve coverage."""

# Standard imports
from unittest.mock import patch
from io import StringIO

# Third-party imports
import pytest

# Local imports
from services.webhook.pr_body_handler import write_pr_description


@pytest.fixture
def mock_pr_payload():
    """Fixture providing a mock pull request payload."""
    return {
        "pull_request": {
            "user": {"login": "gitauto-ai[bot]"},
            "title": "GitAuto: Fix issue with authentication",
            "number": 123,
            "body": "Resolves #456\n\ngit commit -m 'Fix auth issue'",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
            "head": {"ref": "feature-branch"},
        },
        "repository": {
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
        "installation": {"id": 12345},
    }


class TestWritePrDescriptionAdditional:
    """Additional test cases for write_pr_description function."""

    def test_write_pr_description_with_missing_pull_number_keyerror(self, mock_pr_payload):
        """Test PR description generation with missing pull number causes KeyError."""
        # Remove the number key to test KeyError handling
        del mock_pr_payload["pull_request"]["number"]

        with patch("services.webhook.pr_body_handler.get_installation_access_token") as mock_token:
            mock_token.return_value = "ghs_test_token"

            # Execute - should raise KeyError for missing number
            with pytest.raises(KeyError):
                write_pr_description(mock_pr_payload)

            # Verify token retrieval was attempted before KeyError
            mock_token.assert_called_once_with(12345)
