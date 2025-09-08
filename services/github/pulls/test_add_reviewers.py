# pylint: disable=unused-argument,redefined-outer-name
from unittest.mock import Mock, patch
import pytest
import requests
from services.github.pulls.add_reviewers import add_reviewers


@pytest.fixture
def base_args(test_owner, test_repo):
    return {
        "owner": test_owner,
        "repo": test_repo,
        "pr_number": 123,
        "token": "test-token-mock",
        "reviewers": ["reviewer1", "reviewer2", "reviewer3"],
    }


@pytest.fixture
def base_args_no_pr_number(test_owner, test_repo):
    return {
        "owner": test_owner,
        "repo": test_repo,
        "token": "test-token-mock",
        "reviewers": ["reviewer1", "reviewer2"],
    }


@pytest.fixture
def base_args_empty_reviewers(test_owner, test_repo):
    return {
        "owner": test_owner,
        "repo": test_repo,
        "pr_number": 123,
        "token": "test-token-mock",
        "reviewers": [],
    }


@pytest.fixture
def mock_success_response():
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.json.return_value = {
        "requested_reviewers": [{"login": "reviewer1"}, {"login": "reviewer2"}]
    }
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


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("builtins.print")
def test_add_reviewers_success_all_valid(
    mock_print,
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
    mock_success_response,
):
    # All reviewers are collaborators
    mock_check_collaborator.return_value = True
    mock_post.return_value = mock_success_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    result = add_reviewers(base_args)

    assert result is None  # Function returns None on success

    # Verify collaborator checks were called for each reviewer
    assert mock_check_collaborator.call_count == 3
    mock_check_collaborator.assert_any_call(
        owner="gitautoai", repo="gitauto", user="reviewer1", token="test-token-mock"
    )
    mock_check_collaborator.assert_any_call(
        owner="gitautoai", repo="gitauto", user="reviewer2", token="test-token-mock"
    )
    mock_check_collaborator.assert_any_call(
        owner="gitautoai", repo="gitauto", user="reviewer3", token="test-token-mock"
    )

    # Verify print was called with valid reviewers
    mock_print.assert_called_once_with(
        "Adding reviewers: ['reviewer1', 'reviewer2', 'reviewer3']"
    )

    # Verify API call was made
    mock_create_headers.assert_called_once_with(token="test-token-mock")
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls/123/requested_reviewers",
        headers={"Authorization": "Bearer token"},
        json={"reviewers": ["reviewer1", "reviewer2", "reviewer3"]},
        timeout=120,
    )
    mock_success_response.raise_for_status.assert_called_once()


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("builtins.print")
def test_add_reviewers_success_partial_valid(
    mock_print,
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
    mock_success_response,
):
    # Only some reviewers are collaborators
    def collaborator_side_effect(owner, repo, user, token):
        return user in ["reviewer1", "reviewer3"]

    mock_check_collaborator.side_effect = collaborator_side_effect
    mock_post.return_value = mock_success_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    result = add_reviewers(base_args)

    assert result is None

    # Verify collaborator checks were called for each reviewer
    assert mock_check_collaborator.call_count == 3

    # Verify print was called with only valid reviewers
    mock_print.assert_called_once_with("Adding reviewers: ['reviewer1', 'reviewer3']")

    # Verify API call was made with only valid reviewers
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls/123/requested_reviewers",
        headers={"Authorization": "Bearer token"},
        json={"reviewers": ["reviewer1", "reviewer3"]},
        timeout=120,
    )


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_no_valid_reviewers(
    mock_check_collaborator,
    base_args,
):
    # No reviewers are collaborators
    mock_check_collaborator.return_value = False

    result = add_reviewers(base_args)

    assert result is None

    # Verify collaborator checks were called for each reviewer
    assert mock_check_collaborator.call_count == 3


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_empty_reviewers_list(
    mock_check_collaborator,
    base_args_empty_reviewers,
):
    result = add_reviewers(base_args_empty_reviewers)

    assert result is None

    # No collaborator checks should be made for empty list
    mock_check_collaborator.assert_not_called()


def test_add_reviewers_missing_pr_number(base_args_no_pr_number):
    result = add_reviewers(base_args_no_pr_number)

    assert result is None  # handle_exceptions decorator returns None on error


def test_add_reviewers_pr_number_none(test_owner, test_repo):
    base_args = {
        "owner": test_owner,
        "repo": test_repo,
        "pr_number": None,
        "token": "test-token-mock",
        "reviewers": ["reviewer1"],
    }

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("builtins.print")
def test_add_reviewers_http_error(
    mock_print,
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
    mock_error_response,
):
    mock_check_collaborator.return_value = True
    mock_post.return_value = mock_error_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error

    # Verify the API call was attempted
    mock_post.assert_called_once()
    mock_error_response.raise_for_status.assert_called_once()


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_requests_exception(
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
):
    mock_check_collaborator.return_value = True
    mock_post.side_effect = requests.RequestException("Network error")
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error
    mock_post.assert_called_once()


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_create_headers_exception(
    mock_check_collaborator,
    mock_create_headers,
    base_args,
):
    mock_check_collaborator.return_value = True
    mock_create_headers.side_effect = Exception("Header creation error")

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error
    mock_create_headers.assert_called_once_with(token="test-token-mock")


@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_collaborator_check_exception(
    mock_check_collaborator,
    base_args,
):
    mock_check_collaborator.side_effect = Exception("Collaborator check error")

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error
    mock_check_collaborator.assert_called_once()


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("builtins.print")
def test_add_reviewers_single_reviewer(
    mock_print,
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    test_owner,
    test_repo,
    mock_success_response,
):
    base_args = {
        "owner": test_owner,
        "repo": test_repo,
        "pr_number": 456,
        "token": "test-token-mock",
        "reviewers": ["single_reviewer"],
    }

    mock_check_collaborator.return_value = True
    mock_post.return_value = mock_success_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    result = add_reviewers(base_args)

    assert result is None
    mock_print.assert_called_once_with("Adding reviewers: ['single_reviewer']")
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/gitautoai/gitauto/pulls/456/requested_reviewers",
        headers={"Authorization": "Bearer token"},
        json={"reviewers": ["single_reviewer"]},
        timeout=120,
    )


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_422_unprocessable_entity(
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
):
    mock_check_collaborator.return_value = True
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    # Create a 422 response (e.g., reviewer already requested)
    response = Mock(spec=requests.Response)
    response.status_code = 422
    response.reason = "Unprocessable Entity"
    response.text = "Validation Failed"
    http_error = requests.HTTPError("422 Unprocessable Entity")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    mock_post.return_value = response

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error
    mock_post.assert_called_once()


def test_add_reviewers_missing_required_fields():
    # Test with missing owner
    incomplete_args = {
        "repo": "test-repo",
        "pr_number": 123,
        "token": "test-token",
        "reviewers": ["reviewer1"],
    }

    result = add_reviewers(incomplete_args)
    assert result is None  # handle_exceptions decorator returns None on error


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("builtins.print")
def test_add_reviewers_mixed_collaborator_results(
    mock_print,
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
    mock_success_response,
):
    # Mix of collaborators and non-collaborators with some exceptions
    def collaborator_side_effect(owner, repo, user, token):
        if user == "reviewer1":
            return True
        elif user == "reviewer2":
            raise Exception("API error")  # This should be handled by handle_exceptions
        else:  # reviewer3
            return False

    mock_check_collaborator.side_effect = collaborator_side_effect
    mock_post.return_value = mock_success_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    result = add_reviewers(base_args)

    # Should still work with the valid reviewer despite the exception
    assert result is None
    assert (
        mock_check_collaborator.call_count == 2
    )  # Should stop after exception on reviewer2


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_timeout_error(
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
):
    mock_check_collaborator.return_value = True
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_post.side_effect = requests.Timeout("Request timeout")

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error
    mock_post.assert_called_once()


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
def test_add_reviewers_connection_error(
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    base_args,
):
    mock_check_collaborator.return_value = True
    mock_create_headers.return_value = {"Authorization": "Bearer token"}
    mock_post.side_effect = requests.ConnectionError("Connection failed")

    result = add_reviewers(base_args)

    assert result is None  # handle_exceptions decorator returns None on error
    mock_post.assert_called_once()


@patch("services.github.pulls.add_reviewers.create_headers")
@patch("services.github.pulls.add_reviewers.requests.post")
@patch("services.github.pulls.add_reviewers.check_user_is_collaborator")
@patch("builtins.print")
def test_add_reviewers_url_construction(
    mock_print,
    mock_check_collaborator,
    mock_post,
    mock_create_headers,
    mock_success_response,
):
    # Test with different owner/repo/pr_number combinations
    base_args = {
        "owner": "different-owner",
        "repo": "different-repo",
        "pr_number": 999,
        "token": "different-token",
        "reviewers": ["test-reviewer"],
    }

    mock_check_collaborator.return_value = True
    mock_post.return_value = mock_success_response
    mock_create_headers.return_value = {"Authorization": "Bearer token"}

    result = add_reviewers(base_args)

    assert result is None
    mock_post.assert_called_once_with(
        url="https://api.github.com/repos/different-owner/different-repo/pulls/999/requested_reviewers",
        headers={"Authorization": "Bearer token"},
        json={"reviewers": ["test-reviewer"]},
        timeout=120,
    )
    mock_create_headers.assert_called_once_with(token="different-token")
    mock_print.assert_called_once_with("Adding reviewers: ['test-reviewer']")
