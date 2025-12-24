from unittest.mock import MagicMock, patch

from services.github.commits.check_commit_has_skip_ci import check_commit_has_skip_ci


@patch("services.github.commits.check_commit_has_skip_ci.requests.get")
def test_check_commit_has_skip_ci_returns_true(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "commit": {"message": "Fix bug [skip ci]"},
        "sha": "abc123",
    }
    mock_get.return_value = mock_response

    result = check_commit_has_skip_ci(
        owner="test-owner", repo="test-repo", commit_sha="abc123", token="test-token"
    )

    assert result is True
    mock_get.assert_called_once()


@patch("services.github.commits.check_commit_has_skip_ci.requests.get")
def test_check_commit_has_skip_ci_returns_false(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "commit": {"message": "Fix bug"},
        "sha": "abc123",
    }
    mock_get.return_value = mock_response

    result = check_commit_has_skip_ci(
        owner="test-owner", repo="test-repo", commit_sha="abc123", token="test-token"
    )

    assert result is False
    mock_get.assert_called_once()


@patch("services.github.commits.check_commit_has_skip_ci.requests.get")
def test_check_commit_has_skip_ci_with_exception(mock_get):
    mock_get.side_effect = Exception("API error")

    result = check_commit_has_skip_ci(
        owner="test-owner", repo="test-repo", commit_sha="abc123", token="test-token"
    )

    assert result is False
    mock_get.assert_called_once()


@patch("services.github.commits.check_commit_has_skip_ci.requests.get")
def test_check_commit_has_skip_ci_missing_commit_key(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"sha": "abc123"}
    mock_get.return_value = mock_response

    result = check_commit_has_skip_ci(
        owner="test-owner", repo="test-repo", commit_sha="abc123", token="test-token"
    )

    assert result is False
    mock_get.assert_called_once()
