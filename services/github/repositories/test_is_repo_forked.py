from unittest.mock import MagicMock, patch

from services.github.repositories.is_repo_forked import is_repo_forked

MODULE = "services.github.repositories.is_repo_forked"


@patch(f"{MODULE}.create_headers")
@patch(f"{MODULE}.requests.get")
def test_returns_true_for_forked_repo(_mock_get: MagicMock, _mock_headers: MagicMock):
    response = MagicMock()
    response.json.return_value = {"fork": True}
    _mock_get.return_value = response
    assert is_repo_forked(owner="owner", repo="repo", token="token") is True


@patch(f"{MODULE}.create_headers")
@patch(f"{MODULE}.requests.get")
def test_returns_false_for_non_forked_repo(
    _mock_get: MagicMock, _mock_headers: MagicMock
):
    response = MagicMock()
    response.json.return_value = {"fork": False}
    _mock_get.return_value = response
    assert is_repo_forked(owner="owner", repo="repo", token="token") is False


@patch(f"{MODULE}.create_headers")
@patch(f"{MODULE}.requests.get")
def test_returns_false_when_fork_key_missing(
    _mock_get: MagicMock, _mock_headers: MagicMock
):
    response = MagicMock()
    response.json.return_value = {}
    _mock_get.return_value = response
    assert is_repo_forked(owner="owner", repo="repo", token="token") is False


@patch(f"{MODULE}.create_headers")
@patch(f"{MODULE}.requests.get")
def test_returns_false_on_api_error(_mock_get: MagicMock, _mock_headers: MagicMock):
    _mock_get.side_effect = Exception("API error")
    assert is_repo_forked(owner="owner", repo="repo", token="token") is False
