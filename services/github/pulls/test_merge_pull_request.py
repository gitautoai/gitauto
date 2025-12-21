from unittest.mock import MagicMock, patch

from services.github.pulls.merge_pull_request import merge_pull_request


@patch("services.github.pulls.merge_pull_request.requests.put")
def test_merge_pull_request_success(mock_put):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "sha": "abc123",
        "merged": True,
        "message": "Pull Request successfully merged",
    }
    mock_put.return_value = mock_response

    result = merge_pull_request(
        owner="test-owner",
        repo="test-repo",
        pull_number=123,
        token="test-token",
        merge_method="squash",
    )

    assert result is not None
    assert result["merged"] is True
    mock_put.assert_called_once()
    call_args = mock_put.call_args
    assert call_args[1]["json"]["merge_method"] == "squash"


@patch("services.github.pulls.merge_pull_request.requests.put")
def test_merge_pull_request_handles_error(mock_put):
    mock_put.side_effect = Exception("API error")

    result = merge_pull_request(
        owner="test-owner",
        repo="test-repo",
        pull_number=789,
        token="test-token",
    )

    assert result is None
