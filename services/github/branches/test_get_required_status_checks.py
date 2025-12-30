# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.branches.get_required_status_checks import (
    get_required_status_checks,
)


@pytest.fixture
def mock_branch_protection_response():
    return {
        "required_status_checks": {
            "strict": True,
            "contexts": ["ci/circleci: test", "Codecov"],
            "checks": [
                {"context": "CircleCI Checks", "app_id": 12345},
                {"context": "Aikido Security", "app_id": 67890},
            ],
        }
    }


def test_get_required_status_checks_success(
    test_owner, test_repo, test_token, mock_branch_protection_response
):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_branch_protection_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        mock_get.assert_called_once_with(
            url=f"https://api.github.com/repos/{test_owner}/{test_repo}/branches/main/protection",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )
        assert result is not None
        assert set(result) == {
            "ci/circleci: test",
            "Codecov",
            "CircleCI Checks",
            "Aikido Security",
        }


def test_get_required_status_checks_403_no_permission(
    test_owner, test_repo, test_token, capsys
):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        assert result is None
        captured = capsys.readouterr()
        assert "No permission to read branch protection" in captured.out


def test_get_required_status_checks_404_no_protection(
    test_owner, test_repo, test_token, capsys
):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        assert result is None
        captured = capsys.readouterr()
        assert "No branch protection configured" in captured.out


def test_get_required_status_checks_no_required_checks(
    test_owner, test_repo, test_token, capsys
):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"required_status_checks": None}
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        assert result is None
        captured = capsys.readouterr()
        assert "no required status checks configured" in captured.out


def test_get_required_status_checks_only_contexts(test_owner, test_repo, test_token):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "required_status_checks": {
                "strict": True,
                "contexts": ["ci/circleci: test"],
                "checks": [],
            }
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        assert result == ["ci/circleci: test"]


def test_get_required_status_checks_only_checks(test_owner, test_repo, test_token):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "required_status_checks": {
                "strict": False,
                "contexts": [],
                "checks": [{"context": "CircleCI Checks", "app_id": 12345}],
            }
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        assert result == ["CircleCI Checks"]


def test_get_required_status_checks_http_error_500(test_owner, test_repo, test_token):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        assert result is None


def test_get_required_status_checks_network_error(test_owner, test_repo, test_token):
    with patch(
        "services.github.branches.get_required_status_checks.requests.get"
    ) as mock_get, patch(
        "services.github.branches.get_required_status_checks.create_headers"
    ) as mock_headers:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_required_status_checks(
            owner=test_owner, repo=test_repo, branch="main", token=test_token
        )

        assert result is None
