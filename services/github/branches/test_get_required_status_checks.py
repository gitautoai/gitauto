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
        assert result.status_code == 200
        assert result.checks is not None
        assert set(result.checks) == {
            "ci/circleci: test",
            "Codecov",
            "CircleCI Checks",
            "Aikido Security",
        }
        assert result.app_ids == {12345, 67890}
        assert result.strict is True


def test_get_required_status_checks_403_no_permission(
    test_owner, test_repo, test_token
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

        assert result.status_code == 403
        assert result.checks is None
        assert result.app_ids is None
        assert result.strict is True


def test_get_required_status_checks_404_no_protection(
    test_owner, test_repo, test_token
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

        assert result.status_code == 404
        assert not result.checks
        assert result.app_ids is None
        assert result.strict is False


def test_get_required_status_checks_no_required_checks(
    test_owner, test_repo, test_token
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

        assert result.status_code == 200
        assert not result.checks
        assert result.app_ids is None
        assert result.strict is False


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

        assert result.status_code == 200
        assert result.checks == ["ci/circleci: test"]
        assert result.app_ids is None
        assert result.strict is True


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

        assert result.status_code == 200
        assert result.checks == ["CircleCI Checks"]
        assert result.app_ids == {12345}
        assert result.strict is False


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

        assert result.status_code == 201
        assert result.checks is None
        assert result.strict is True


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

        assert result.status_code == 201
        assert result.checks is None
        assert result.strict is True
