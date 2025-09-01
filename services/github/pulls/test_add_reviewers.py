# pylint: disable=unused-argument,redefined-outer-name
from unittest.mock import Mock, patch
import pytest
import requests
from services.github.pulls.add_reviewers import add_reviewers


@pytest.fixture
def base_args_with_pr_number(create_test_base_args):
    return create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        pr_number=123,
        token="test-token",
        reviewers=["reviewer1", "reviewer2", "reviewer3"],
    )


@pytest.fixture
def base_args_without_pr_number(create_test_base_args):
    return create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        reviewers=["reviewer1", "reviewer2"],
    )


@pytest.fixture
def mock_successful_response():
    response = Mock(spec=requests.Response)
    response.status_code = 200
    return response


@pytest.fixture
def mock_error_response():
    response = Mock(spec=requests.Response)
    response.status_code = 500
    response.reason = "Internal Server Error"
    response.text = "Server Error"
    http_error = requests.HTTPError("500 Server Error")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    return response


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("builtins.print")
def test_add_reviewers_success_all_valid_reviewers(
    mock_print,
    mock_post,
    mock_create_headers,
    mock_check_collaborator,
    base_args_with_pr_number,
    mock_successful_response,
):
    # Setup mocks
    mock_check_collaborator.return_value = True
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_post.return_value = mock_successful_response

    # Call the function
    result = add_reviewers(base_args_with_pr_number)

    # Assertions
    assert result is None  # Function returns None on success
    
    # Check that all reviewers were checked for collaboration
    assert mock_check_collaborator.call_count == 3
    mock_check_collaborator.assert_any_call(
        owner="test-owner", repo="test-repo", user="reviewer1", token="test-token"
    )
    mock_check_collaborator.assert_any_call(
        owner="test-owner", repo="test-repo", user="reviewer2", token="test-token"
    )
    mock_check_collaborator.assert_any_call(
        owner="test-owner", repo="test-repo", user="reviewer3", token="test-token"
    )
    
    # Check print statement
    mock_print.assert_called_once_with("Adding reviewers: ['reviewer1', 'reviewer2', 'reviewer3']")
    
    # Check API call
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/123/requested_reviewers",
        headers={"Authorization": "Bearer token"},
        json={"reviewers": ["reviewer1", "reviewer2", "reviewer3"]},
        timeout=120,
    )
    mock_successful_response.raise_for_status.assert_called_once()


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("builtins.print")
def test_add_reviewers_success_some_valid_reviewers(
    mock_print,
    mock_post,
    mock_create_headers,
    mock_check_collaborator,
    base_args_with_pr_number,
    mock_successful_response,
):
    # Setup mocks - only reviewer1 and reviewer3 are collaborators
    def mock_collaborator_check(owner, repo, user, token):
        return user in ["reviewer1", "reviewer3"]
    
    mock_check_collaborator.side_effect = mock_collaborator_check
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_post.return_value = mock_successful_response

    # Call the function
    result = add_reviewers(base_args_with_pr_number)

    # Assertions
    assert result is None
    
    # Check that all reviewers were checked
    assert mock_check_collaborator.call_count == 3
    
    # Check print statement shows only valid reviewers
    mock_print.assert_called_once_with("Adding reviewers: ['reviewer1', 'reviewer3']")
    
    # Check API call with only valid reviewers
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/123/requested_reviewers",
        headers={"Authorization": "Bearer token"},
        json={"reviewers": ["reviewer1", "reviewer3"]},
        timeout=120,
    )


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_no_valid_reviewers(
    mock_check_collaborator, base_args_with_pr_number
):
    # Setup mocks - no reviewers are collaborators
    mock_check_collaborator.return_value = False

    # Call the function
    result = add_reviewers(base_args_with_pr_number)

    # Assertions
    assert result is None
    
    # Check that all reviewers were checked
    assert mock_check_collaborator.call_count == 3
    
    # No API call should be made since no valid reviewers
    with patch("services.github.pulls.add_reviewers.requests.post") as mock_post:
        with patch("services.github.pulls.add_reviewers.create_headers") as mock_create_headers:
            # Re-run to verify no API calls
            add_reviewers(base_args_with_pr_number)
            mock_create_headers.assert_not_called()
            mock_post.assert_not_called()


def test_add_reviewers_missing_pr_number(base_args_without_pr_number):
    # Call the function without pr_number
    result = add_reviewers(base_args_without_pr_number)

    # Should return None due to exception handling
    assert result is None


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("builtins.print")
def test_add_reviewers_empty_reviewers_list(
    mock_print,
    mock_post,
    mock_create_headers,
    mock_check_collaborator,
    create_test_base_args,
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        pr_number=123,
        token="test-token",
        reviewers=[],
    )

    # Call the function
    result = add_reviewers(base_args)

    # Assertions
    assert result is None
    
    # No collaborator checks should be made
    mock_check_collaborator.assert_not_called()
    
    # No API calls should be made
    mock_create_headers.assert_not_called()
    mock_post.assert_not_called()
    mock_print.assert_not_called()


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("builtins.print")
def test_add_reviewers_http_error(
    mock_print,
    mock_post,
    mock_create_headers,
    mock_check_collaborator,
    base_args_with_pr_number,
    mock_error_response,
):
    # Setup mocks
    mock_check_collaborator.return_value = True
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_post.return_value = mock_error_response

    # Call the function
    result = add_reviewers(base_args_with_pr_number)

    # Should return None due to exception handling
    assert result is None
    
    # Verify the API call was made
    mock_post.assert_called_once()
    mock_error_response.raise_for_status.assert_called_once()


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("builtins.print")
def test_add_reviewers_requests_exception(
    mock_print,
    mock_post,
    mock_create_headers,
    mock_check_collaborator,
    base_args_with_pr_number,
):
    # Setup mocks
    mock_check_collaborator.return_value = True
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_post.side_effect = requests.RequestException("Network error")

    # Call the function
    result = add_reviewers(base_args_with_pr_number)

    # Should return None due to exception handling
    assert result is None
    
    # Verify the API call was attempted
    mock_post.assert_called_once()


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_collaborator_check_exception(
    mock_check_collaborator, base_args_with_pr_number
):
    # Setup mock to raise exception
    mock_check_collaborator.side_effect = Exception("Collaborator check failed")

    # Call the function
    result = add_reviewers(base_args_with_pr_number)

    # Should return None due to exception handling
    assert result is None


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("services.github.pulls.add_reviewers.create_headers")
def test_add_reviewers_create_headers_exception(
    mock_create_headers, mock_check_collaborator, base_args_with_pr_number
):
    # Setup mocks
    mock_check_collaborator.return_value = True
    mock_create_headers.side_effect = Exception("Header creation failed")

    # Call the function
    result = add_reviewers(base_args_with_pr_number)

    # Should return None due to exception handling
    assert result is None


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("builtins.print")
def test_add_reviewers_single_reviewer(
    mock_print,
    mock_post,
    mock_create_headers,
    mock_check_collaborator,
    create_test_base_args,
    mock_successful_response,
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        pr_number=456,
        token="test-token",
        reviewers=["single-reviewer"],
    )

    # Setup mocks
    mock_check_collaborator.return_value = True
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_post.return_value = mock_successful_response

    # Call the function
    result = add_reviewers(base_args)

    # Assertions
    assert result is None
    mock_check_collaborator.assert_called_once_with(
        owner="test-owner", repo="test-repo", user="single-reviewer", token="test-token"
    )
    mock_print.assert_called_once_with("Adding reviewers: ['single-reviewer']")
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/456/requested_reviewers",
        headers={"Authorization": "Bearer token"},
        json={"reviewers": ["single-reviewer"]},
        timeout=120,
    )
