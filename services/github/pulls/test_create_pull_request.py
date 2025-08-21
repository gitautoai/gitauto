from unittest.mock import Mock, patch
import pytest
import requests
from services.github.pulls.create_pull_request import create_pull_request
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def base_args():
    return {
        "owner": OWNER,
        "repo": REPO,
        "base_branch": "main",
        "new_branch": "feature-branch",
        "token": TOKEN,
        "reviewers": ["reviewer1", "reviewer2"]
    }


@pytest.fixture
def mock_response():
    response = Mock(spec=requests.Response)
    response.status_code = 201
    response.json.return_value = {
        "number": 123,
        "html_url": "https://github.com/owner/repo/pull/123"
    }
    response.url = "https://api.github.com/repos/owner/repo/pulls"
    return response


@pytest.fixture
def mock_422_response():
    response = Mock(spec=requests.Response)
    response.status_code = 422
    response.url = "https://api.github.com/repos/owner/repo/pulls"
    return response


@pytest.fixture
def mock_error_response():
    response = Mock(spec=requests.Response)
    response.status_code = 500
    http_error = requests.HTTPError("500 Server Error")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    return response


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_success(mock_post, mock_create_headers, mock_add_reviewers, base_args, mock_response):
    mock_post.return_value = mock_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    
    result = create_pull_request("Test body", "Test title", base_args)
    
    assert result == "https://github.com/owner/repo/pull/123"
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls",
        headers={"Authorization": "Bearer token"},
        json={"title": "Test title", "body": "Test body", "head": "feature-branch", "base": "main"},
        timeout=120
    )
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    
    expected_base_args = base_args.copy()
    expected_base_args["pr_number"] = 123
    mock_add_reviewers.assert_called_once_with(base_args=expected_base_args)


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
@patch("builtins.print")
def test_create_pull_request_422_error(mock_print, mock_post, mock_create_headers, mock_add_reviewers, base_args, mock_422_response):
    mock_post.return_value = mock_422_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    
    result = create_pull_request("Test body", "Test title", base_args)
    
    assert result is None
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls",
        headers={"Authorization": "Bearer token"},
        json={"title": "Test title", "body": "Test body", "head": "feature-branch", "base": "main"},
        timeout=120
    )
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_422_response.raise_for_status.assert_not_called()
    mock_422_response.json.assert_not_called()
    mock_add_reviewers.assert_not_called()
    
    expected_msg = "create_pull_request encountered an HTTPError: 422 Client Error: Unprocessable Entity for url: https://api.github.com/repos/owner/repo/pulls, which is because no commits between the base branch and the working branch."
    mock_print.assert_called_once_with(expected_msg)


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_http_error(mock_post, mock_create_headers, mock_add_reviewers, base_args, mock_error_response):
    mock_post.return_value = mock_error_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    
    result = create_pull_request("Test body", "Test title", base_args)
    
    assert result is None
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls",
        headers={"Authorization": "Bearer token"},
        json={"title": "Test title", "body": "Test body", "head": "feature-branch", "base": "main"},
        timeout=120
    )
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_error_response.raise_for_status.assert_called_once()
    mock_error_response.json.assert_not_called()
    mock_add_reviewers.assert_not_called()


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_json_error(mock_post, mock_create_headers, mock_add_reviewers, base_args, mock_response):
    mock_post.return_value = mock_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    result = create_pull_request("Test body", "Test title", base_args)
    
    assert result is None
    mock_post.assert_called_once()
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    mock_add_reviewers.assert_not_called()


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_add_reviewers_error(mock_post, mock_create_headers, mock_add_reviewers, base_args, mock_response):
    mock_post.return_value = mock_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_add_reviewers.side_effect = Exception("Reviewer error")
    
    result = create_pull_request("Test body", "Test title", base_args)
    
    assert result is None
    mock_post.assert_called_once()
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    
    expected_base_args = base_args.copy()
    expected_base_args["pr_number"] = 123
    mock_add_reviewers.assert_called_once_with(base_args=expected_base_args)


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_empty_strings(mock_post, mock_create_headers, mock_add_reviewers, base_args, mock_response):
    mock_post.return_value = mock_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    
    result = create_pull_request("", "", base_args)
    
    assert result == "https://github.com/owner/repo/pull/123"
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls",
        headers={"Authorization": "Bearer token"},
        json={"title": "", "body": "", "head": "feature-branch", "base": "main"},
        timeout=120
    )
    
    expected_base_args = base_args.copy()
    expected_base_args["pr_number"] = 123
    mock_add_reviewers.assert_called_once_with(base_args=expected_base_args)


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_different_branches(mock_post, mock_create_headers, mock_add_reviewers, base_args, mock_response):
    mock_post.return_value = mock_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    base_args["base_branch"] = "develop"
    base_args["new_branch"] = "feature/new-feature"
    
    result = create_pull_request("Feature body", "Feature title", base_args)
    
    assert result == "https://github.com/owner/repo/pull/123"
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls",
        headers={"Authorization": "Bearer token"},
        json={"title": "Feature title", "body": "Feature body", "head": "feature/new-feature", "base": "develop"},
        timeout=120
    )


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_requests_exception(mock_post, mock_create_headers, mock_add_reviewers, base_args):
    mock_post.side_effect = requests.RequestException("Network error")
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    
    result = create_pull_request("Test body", "Test title", base_args)
    
    assert result is None
    mock_post.assert_called_once()
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_add_reviewers.assert_not_called()


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_create_headers_exception(mock_post, mock_create_headers, mock_add_reviewers, base_args):
    mock_create_headers.side_effect = Exception("Header creation error")
    
    result = create_pull_request("Test body", "Test title", base_args)
    
    assert result is None
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_post.assert_not_called()
    mock_add_reviewers.assert_not_called()


@patch("services.github.pulls.create_pull_request.add_reviewers")
@patch("services.github.pulls.create_pull_request.create_headers")
@patch("services.github.pulls.create_pull_request.requests.post")
def test_create_pull_request_key_error_in_base_args(mock_post, mock_create_headers, mock_add_reviewers):
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    incomplete_base_args = {"owner": OWNER, "repo": REPO}
    
    result = create_pull_request("Test body", "Test title", incomplete_base_args)
    
    assert result is None
    mock_create_headers.assert_not_called()
    mock_post.assert_not_called()
    mock_add_reviewers.assert_not_called()
