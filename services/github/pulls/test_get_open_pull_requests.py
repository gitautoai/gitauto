from unittest.mock import Mock, patch
from services.github.pulls.get_open_pull_requests import get_open_pull_requests


@patch(
    "services.github.pulls.get_open_pull_requests.GITHUB_APP_USER_NAME",
    "gitauto-ai[bot]",
)
def test_get_open_pull_requests_success():
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "number": 123,
            "title": "Test PR 1",
            "head": {"ref": "feature-1"},
            "base": {"ref": "main"},
            "user": {"login": "gitauto-ai[bot]"},
        },
        {
            "number": 124,
            "title": "Test PR 2",
            "head": {"ref": "feature-2"},
            "base": {"ref": "main"},
            "user": {"login": "gitauto-ai[bot]"},
        },
    ]
    mock_response.raise_for_status = Mock()

    with patch("requests.get") as mock_get:
        mock_get.side_effect = [
            mock_response,
            Mock(json=lambda: [], raise_for_status=Mock()),
        ]

        result = get_open_pull_requests(
            owner="test-owner",
            repo="test-repo",
            target_branch="main",
            token="test-token",
        )

        assert len(result) == 2
        assert result[0]["number"] == 123
        assert result[1]["number"] == 124
        assert mock_get.call_count == 2


@patch(
    "services.github.pulls.get_open_pull_requests.GITHUB_APP_USER_NAME",
    "gitauto-ai[bot]",
)
def test_get_open_pull_requests_pagination():
    first_page = [
        {"number": i, "user": {"login": "gitauto-ai[bot]"}} for i in range(100)
    ]
    second_page = [
        {"number": i, "user": {"login": "gitauto-ai[bot]"}} for i in range(100, 150)
    ]

    mock_response_1 = Mock()
    mock_response_1.json.return_value = first_page
    mock_response_1.raise_for_status = Mock()

    mock_response_2 = Mock()
    mock_response_2.json.return_value = second_page
    mock_response_2.raise_for_status = Mock()

    mock_response_3 = Mock()
    mock_response_3.json.return_value = []
    mock_response_3.raise_for_status = Mock()

    with patch("requests.get") as mock_get:
        mock_get.side_effect = [mock_response_1, mock_response_2, mock_response_3]

        result = get_open_pull_requests(
            owner="test-owner",
            repo="test-repo",
            target_branch="develop",
            token="test-token",
        )

        assert len(result) == 150
        assert mock_get.call_count == 3


def test_get_open_pull_requests_empty():
    mock_response = Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_response):
        result = get_open_pull_requests(
            owner="test-owner",
            repo="test-repo",
            target_branch="main",
            token="test-token",
        )

        assert not result


def test_get_open_pull_requests_error():
    with patch("requests.get", side_effect=Exception("API error")):
        result = get_open_pull_requests(
            owner="test-owner",
            repo="test-repo",
            target_branch="main",
            token="test-token",
        )

        assert not result


@patch(
    "services.github.pulls.get_open_pull_requests.GITHUB_APP_USER_NAME",
    "gitauto-ai[bot]",
)
def test_get_open_pull_requests_filters_non_gitauto_prs():
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "number": 123,
            "title": "GitAuto PR",
            "head": {"ref": "feature-1"},
            "base": {"ref": "main"},
            "user": {"login": "gitauto-ai[bot]"},
        },
        {
            "number": 124,
            "title": "Developer PR",
            "head": {"ref": "feature-2"},
            "base": {"ref": "main"},
            "user": {"login": "developer123"},
        },
        {
            "number": 125,
            "title": "Another Bot PR",
            "head": {"ref": "feature-3"},
            "base": {"ref": "main"},
            "user": {"login": "renovate[bot]"},
        },
    ]
    mock_response.raise_for_status = Mock()

    with patch("requests.get") as mock_get:
        mock_get.side_effect = [
            mock_response,
            Mock(json=lambda: [], raise_for_status=Mock()),
        ]

        result = get_open_pull_requests(
            owner="test-owner",
            repo="test-repo",
            target_branch="main",
            token="test-token",
        )

        assert len(result) == 1
        assert result[0]["number"] == 123
        assert result[0]["user"]["login"] == "gitauto-ai[bot]"


@patch(
    "services.github.pulls.get_open_pull_requests.GITHUB_APP_USER_NAME",
    "gitauto-ai[bot]",
)
def test_get_open_pull_requests_no_gitauto_prs():
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "number": 124,
            "title": "Developer PR",
            "head": {"ref": "feature-2"},
            "base": {"ref": "main"},
            "user": {"login": "developer123"},
        },
        {
            "number": 125,
            "title": "Another Bot PR",
            "head": {"ref": "feature-3"},
            "base": {"ref": "main"},
            "user": {"login": "renovate[bot]"},
        },
    ]
    mock_response.raise_for_status = Mock()

    with patch("requests.get") as mock_get:
        mock_get.side_effect = [
            mock_response,
            Mock(json=lambda: [], raise_for_status=Mock()),
        ]

        result = get_open_pull_requests(
            owner="test-owner",
            repo="test-repo",
            target_branch="main",
            token="test-token",
        )

        assert not result
