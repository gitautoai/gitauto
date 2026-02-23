from unittest.mock import MagicMock, patch

from services.github.users.get_email_from_commits import get_email_from_commits


@patch("services.github.users.get_email_from_commits.requests.get")
def test_returns_first_non_noreply_email(mock_get: MagicMock):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.return_value = [
        {"commit": {"author": {"email": "wes@gitauto.ai"}}},
    ]
    result = get_email_from_commits(
        owner="gitautoai", repo="gitauto", username="wes", token="tok"
    )
    assert result == "wes@gitauto.ai"


@patch("services.github.users.get_email_from_commits.requests.get")
def test_skips_noreply_email(mock_get: MagicMock):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.return_value = [
        {"commit": {"author": {"email": "123+user@users.noreply.github.com"}}},
        {"commit": {"author": {"email": "real@example.com"}}},
    ]
    result = get_email_from_commits(owner="o", repo="r", username="u", token="t")
    assert result == "real@example.com"


@patch("services.github.users.get_email_from_commits.requests.get")
def test_returns_none_when_all_noreply(mock_get: MagicMock):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.return_value = [
        {"commit": {"author": {"email": "123+user@users.noreply.github.com"}}},
    ]
    result = get_email_from_commits(owner="o", repo="r", username="u", token="t")
    assert result is None


@patch("services.github.users.get_email_from_commits.requests.get")
def test_returns_none_when_no_commits(mock_get: MagicMock):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.return_value = []
    result = get_email_from_commits(owner="o", repo="r", username="u", token="t")
    assert result is None


@patch("services.github.users.get_email_from_commits.requests.get")
def test_returns_none_on_api_error(mock_get: MagicMock):
    mock_get.side_effect = Exception("API error")
    result = get_email_from_commits(owner="o", repo="r", username="u", token="t")
    assert result is None
