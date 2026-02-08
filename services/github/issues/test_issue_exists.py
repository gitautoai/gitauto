from unittest.mock import MagicMock, patch

from services.github.issues.issue_exists import issue_exists


@patch("services.github.issues.issue_exists.requests.get")
@patch("services.github.issues.issue_exists.create_headers")
def test_returns_true_when_issue_found(mock_headers, mock_get):
    mock_headers.return_value = {"Authorization": "Bearer token"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total_count": 1}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = issue_exists(
        owner="test", repo="test", token="token", title="Fix something"
    )

    assert result is True
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args.kwargs
    assert "Fix something" in call_kwargs["params"]["q"]


@patch("services.github.issues.issue_exists.requests.get")
@patch("services.github.issues.issue_exists.create_headers")
def test_returns_false_when_no_issue(mock_headers, mock_get):
    mock_headers.return_value = {"Authorization": "Bearer token"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total_count": 0}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = issue_exists(
        owner="test", repo="test", token="token", title="Fix something"
    )

    assert result is False


@patch("services.github.issues.issue_exists.requests.get")
@patch("services.github.issues.issue_exists.create_headers")
def test_returns_false_on_error(mock_headers, mock_get):
    mock_headers.return_value = {"Authorization": "Bearer token"}
    mock_get.side_effect = RuntimeError("API error")

    result = issue_exists(
        owner="test", repo="test", token="token", title="Fix something"
    )

    assert result is False
