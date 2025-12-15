from unittest.mock import Mock, patch
from services.github.pulls.update_pull_request_branch import update_pull_request_branch


def test_update_pull_request_branch_success():
    mock_response = Mock()
    mock_response.status_code = 202

    with patch("requests.put", return_value=mock_response) as mock_put:
        status, error = update_pull_request_branch(
            owner="test-owner", repo="test-repo", pull_number=123, token="test-token"
        )

        assert status == "updated"
        assert error is None
        mock_put.assert_called_once()
        _, kwargs = mock_put.call_args
        assert "/repos/test-owner/test-repo/pulls/123/update-branch" in kwargs["url"]


def test_update_pull_request_branch_error():
    with patch("requests.put", side_effect=Exception("API error")):
        status, error = update_pull_request_branch(
            owner="test-owner", repo="test-repo", pull_number=123, token="test-token"
        )

        assert status == "failed"
        assert error == "Unknown error"


def test_update_pull_request_branch_already_up_to_date():
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.json.return_value = {
        "message": "There are no new commits on the base branch."
    }

    with patch("requests.put", return_value=mock_response):
        status, error = update_pull_request_branch(
            owner="test-owner", repo="test-repo", pull_number=123, token="test-token"
        )

        assert status == "up_to_date"
        assert error is None


def test_update_pull_request_branch_http_error():
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"message": "Merge conflict detected"}

    with patch("requests.put", return_value=mock_response):
        status, error = update_pull_request_branch(
            owner="test-owner", repo="test-repo", pull_number=123, token="test-token"
        )

        assert status == "failed"
        assert error is not None
        assert "422" in error
        assert "Merge conflict detected" in error
