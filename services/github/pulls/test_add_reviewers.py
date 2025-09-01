# pylint: disable=unused-argument,redefined-outer-name
from unittest.mock import Mock, patch
import pytest
import requests
from services.github.pulls.add_reviewers import add_reviewers


@pytest.fixture
def mock_check_user_is_collaborator():
    """Fixture to mock check_user_is_collaborator function."""
    with patch(
        "services.github.pulls.add_reviewers.check_user_is_collaborator"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.pulls.add_reviewers.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test-token"}
        yield mock


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post function."""
    with patch("services.github.pulls.add_reviewers.requests.post") as mock:
        yield mock


@pytest.fixture
def mock_print():
    """Fixture to mock print function."""
    with patch("builtins.print") as mock:
        yield mock


@pytest.fixture
def base_args_with_pr_number(create_test_base_args):
    """Base args with pr_number for testing."""
    return create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        pr_number=123,
        token="test-token",
        reviewers=["reviewer1", "reviewer2", "reviewer3"],
    )


@pytest.fixture
def base_args_without_pr_number(create_test_base_args):
    """Base args without pr_number for testing."""
    return create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        reviewers=["reviewer1", "reviewer2"],
    )


@pytest.fixture
def successful_response():
    """Mock successful HTTP response."""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    return response


@pytest.fixture
def error_response():
    """Mock error HTTP response."""
    response = Mock(spec=requests.Response)
    response.status_code = 500
    response.reason = "Internal Server Error"
    response.text = "Server Error"
    http_error = requests.HTTPError("500 Server Error")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    return response


def test_add_reviewers_success_all_valid_reviewers(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    base_args_with_pr_number,
    successful_response,
):
    """Test successful addition of reviewers when all are valid collaborators."""
    # Setup mocks
    mock_check_user_is_collaborator.return_value = True
    mock_requests_post.return_value = successful_response

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert
    assert result is None  # Function returns None on success
    
    # Verify all reviewers were checked for collaboration
    assert mock_check_user_is_collaborator.call_count == 3
    mock_check_user_is_collaborator.assert_any_call(
        owner="test-owner", repo="test-repo", user="reviewer1", token="test-token"
    )
    mock_check_user_is_collaborator.assert_any_call(
        owner="test-owner", repo="test-repo", user="reviewer2", token="test-token"
    )
    mock_check_user_is_collaborator.assert_any_call(
        owner="test-owner", repo="test-repo", user="reviewer3", token="test-token"
    )
    
    # Verify print statement
    mock_print.assert_called_once_with("Adding reviewers: ['reviewer1', 'reviewer2', 'reviewer3']")
    
    # Verify API call
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/123/requested_reviewers",
        headers={"Authorization": "Bearer test-token"},
        json={"reviewers": ["reviewer1", "reviewer2", "reviewer3"]},
        timeout=120,
    )
    successful_response.raise_for_status.assert_called_once()


def test_add_reviewers_success_some_valid_reviewers(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    base_args_with_pr_number,
    successful_response,
):
    """Test successful addition when only some reviewers are valid collaborators."""
    # Setup mocks - only reviewer1 and reviewer3 are collaborators
    def mock_collaborator_check(owner, repo, user, token):
        return user in ["reviewer1", "reviewer3"]
    
    mock_check_user_is_collaborator.side_effect = mock_collaborator_check
    mock_requests_post.return_value = successful_response

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert
    assert result is None
    
    # Verify all reviewers were checked
    assert mock_check_user_is_collaborator.call_count == 3
    
    # Verify print statement shows only valid reviewers
    mock_print.assert_called_once_with("Adding reviewers: ['reviewer1', 'reviewer3']")
    
    # Verify API call with only valid reviewers
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/123/requested_reviewers",
        headers={"Authorization": "Bearer test-token"},
        json={"reviewers": ["reviewer1", "reviewer3"]},
        timeout=120,
    )


def test_add_reviewers_no_valid_reviewers(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    base_args_with_pr_number,
):
    """Test behavior when no reviewers are valid collaborators."""
    # Setup mocks - no reviewers are collaborators
    mock_check_user_is_collaborator.return_value = False

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert
    assert result is None
    
    # Verify all reviewers were checked
    assert mock_check_user_is_collaborator.call_count == 3
    
    # Verify no API calls were made since no valid reviewers
    mock_create_headers.assert_not_called()
    mock_requests_post.assert_not_called()
    mock_print.assert_not_called()


def test_add_reviewers_missing_pr_number(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    base_args_without_pr_number,
):
    """Test behavior when pr_number is missing from base_args."""
    # Execute
    result = add_reviewers(base_args_without_pr_number)

    # Assert - should return None due to exception handling
    assert result is None
    
    # Verify no API calls were made
    mock_check_user_is_collaborator.assert_not_called()
    mock_create_headers.assert_not_called()
    mock_requests_post.assert_not_called()


def test_add_reviewers_empty_reviewers_list(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    create_test_base_args,
):
    """Test behavior when reviewers list is empty."""
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        pr_number=123,
        token="test-token",
        reviewers=[],
    )

    # Execute
    result = add_reviewers(base_args)

    # Assert
    assert result is None
    
    # Verify no operations were performed
    mock_check_user_is_collaborator.assert_not_called()
    mock_create_headers.assert_not_called()
    mock_requests_post.assert_not_called()
    mock_print.assert_not_called()


def test_add_reviewers_http_error(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    base_args_with_pr_number,
    error_response,
):
    """Test behavior when HTTP error occurs during API call."""
    # Setup mocks
    mock_check_user_is_collaborator.return_value = True
    mock_requests_post.return_value = error_response

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert - should return None due to exception handling
    assert result is None
    
    # Verify the API call was made and error was raised
    mock_requests_post.assert_called_once()
    error_response.raise_for_status.assert_called_once()


def test_add_reviewers_requests_exception(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    base_args_with_pr_number,
):
    """Test behavior when requests raises an exception."""
    # Setup mocks
    mock_check_user_is_collaborator.return_value = True
    mock_requests_post.side_effect = requests.RequestException("Network error")

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert - should return None due to exception handling
    assert result is None
    
    # Verify the API call was attempted
    mock_requests_post.assert_called_once()


def test_add_reviewers_collaborator_check_exception(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    base_args_with_pr_number,
):
    """Test behavior when collaborator check raises an exception."""
    # Setup mock to raise exception
    mock_check_user_is_collaborator.side_effect = Exception("Collaborator check failed")

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert - should return None due to exception handling
    assert result is None
    
    # Verify no API calls were made
    mock_create_headers.assert_not_called()
    mock_requests_post.assert_not_called()


def test_add_reviewers_create_headers_exception(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    base_args_with_pr_number,
):
    """Test behavior when create_headers raises an exception."""
    # Setup mocks
    mock_check_user_is_collaborator.return_value = True
    mock_create_headers.side_effect = Exception("Header creation failed")

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert - should return None due to exception handling
    assert result is None
    
    # Verify no post request was made
    mock_requests_post.assert_not_called()


def test_add_reviewers_single_reviewer(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    create_test_base_args,
    successful_response,
):
    """Test behavior with a single reviewer."""
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        pr_number=456,
        token="test-token",
        reviewers=["single-reviewer"],
    )

    # Setup mocks
    mock_check_user_is_collaborator.return_value = True
    mock_requests_post.return_value = successful_response

    # Execute
    result = add_reviewers(base_args)

    # Assert
    assert result is None
    mock_check_user_is_collaborator.assert_called_once_with(
        owner="test-owner", repo="test-repo", user="single-reviewer", token="test-token"
    )
    mock_print.assert_called_once_with("Adding reviewers: ['single-reviewer']")
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/456/requested_reviewers",
        headers={"Authorization": "Bearer test-token"},
        json={"reviewers": ["single-reviewer"]},
        timeout=120,
    )


def test_add_reviewers_constructs_correct_url(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    create_test_base_args,
    successful_response,
):
    """Test that function constructs the correct GitHub API URL."""
    base_args = create_test_base_args(
        owner="special-owner",
        repo="special-repo",
        pr_number=789,
        token="special-token",
        reviewers=["test-reviewer"],
    )

    # Setup mocks
    mock_check_user_is_collaborator.return_value = True
    mock_requests_post.return_value = successful_response

    # Execute
    add_reviewers(base_args)

    # Assert
    expected_url = "https://api.github.com/repos/special-owner/special-repo/pulls/789/requested_reviewers"
    mock_requests_post.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test-token"},
        json={"reviewers": ["test-reviewer"]},
        timeout=120,
    )


@pytest.mark.parametrize(
    "collaborator_results,expected_valid_reviewers",
    [
        ([True, True, True], ["reviewer1", "reviewer2", "reviewer3"]),
        ([True, False, True], ["reviewer1", "reviewer3"]),
        ([False, True, False], ["reviewer2"]),
        ([False, False, False], []),
    ],
)
def test_add_reviewers_various_collaborator_combinations(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    base_args_with_pr_number,
    successful_response,
    collaborator_results,
    expected_valid_reviewers,
):
    """Test various combinations of collaborator check results."""
    # Setup mocks
    mock_check_user_is_collaborator.side_effect = collaborator_results
    mock_requests_post.return_value = successful_response

    # Execute
    result = add_reviewers(base_args_with_pr_number)

    # Assert
    assert result is None
    
    if expected_valid_reviewers:
        # Should make API call with valid reviewers
        mock_print.assert_called_once_with(f"Adding reviewers: {expected_valid_reviewers}")
        mock_requests_post.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123/requested_reviewers",
            headers={"Authorization": "Bearer test-token"},
            json={"reviewers": expected_valid_reviewers},
            timeout=120,
        )
    else:
        # Should not make API call if no valid reviewers
        mock_print.assert_not_called()
        mock_requests_post.assert_not_called()


def test_add_reviewers_with_special_characters_in_params(
    mock_check_user_is_collaborator,
    mock_create_headers,
    mock_requests_post,
    mock_print,
    create_test_base_args,
    successful_response,
):
    """Test that function handles special characters in parameters correctly."""
    base_args = create_test_base_args(
        owner="test-owner-123",
        repo="test.repo_name",
        pr_number=999,
        token="ghp_1234567890abcdef",
        reviewers=["user-name_123", "user.name"],
    )

    # Setup mocks
    mock_check_user_is_collaborator.return_value = True
    mock_requests_post.return_value = successful_response

    # Execute
    result = add_reviewers(base_args)

    # Assert
    assert result is None
    expected_url = "https://api.github.com/repos/test-owner-123/test.repo_name/pulls/999/requested_reviewers"
    mock_requests_post.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test-token"},
        json={"reviewers": ["user-name_123", "user.name"]},
        timeout=120,
    )