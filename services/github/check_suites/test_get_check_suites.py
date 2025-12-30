# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.check_suites.get_check_suites import get_check_suites


@pytest.fixture
def mock_check_suites_response():
    return {
        "total_count": 2,
        "check_suites": [
            {
                "id": 53232653600,
                "status": "completed",
                "conclusion": "failure",
                "app": {"name": "CircleCI Checks", "slug": "circleci-checks"},
            },
            {
                "id": 53232653801,
                "status": "completed",
                "conclusion": "success",
                "app": {"name": "Aikido PR Checks", "slug": "aikido"},
            },
        ],
    }


def test_get_check_suites_success(
    test_owner, test_repo, test_token, mock_check_suites_response
):
    with patch(
        "services.github.check_suites.get_check_suites.requests.get"
    ) as mock_get, patch(
        "services.github.check_suites.get_check_suites.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_check_suites_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_check_suites(
            owner=test_owner, repo=test_repo, ref="abc123", token=test_token
        )

        mock_get.assert_called_once_with(
            url=f"https://api.github.com/repos/{test_owner}/{test_repo}/commits/abc123/check-suites",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == mock_check_suites_response["check_suites"]


def test_get_check_suites_headers_creation(test_owner, test_repo):
    with patch(
        "services.github.check_suites.get_check_suites.requests.get"
    ) as mock_get, patch(
        "services.github.check_suites.get_check_suites.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = {"check_suites": []}
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_token"}

        get_check_suites(
            owner=test_owner, repo=test_repo, ref="abc123", token="custom_token_123"
        )

        mock_headers.assert_called_once_with(token="custom_token_123")


def test_get_check_suites_http_error_404(test_owner, test_repo, test_token):
    with patch(
        "services.github.check_suites.get_check_suites.requests.get"
    ) as mock_get, patch(
        "services.github.check_suites.get_check_suites.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_check_suites(
            owner=test_owner, repo=test_repo, ref="nonexistent", token=test_token
        )

        assert result is None


def test_get_check_suites_network_error(test_owner, test_repo, test_token):
    with patch(
        "services.github.check_suites.get_check_suites.requests.get"
    ) as mock_get, patch(
        "services.github.check_suites.get_check_suites.create_headers"
    ) as mock_headers:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_check_suites(
            owner=test_owner, repo=test_repo, ref="abc123", token=test_token
        )

        assert result is None
