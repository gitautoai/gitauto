# pylint: disable=unused-argument

from unittest.mock import patch, MagicMock
import requests
import pytest
from services.github.reactions.add_reaction_to_issue import add_reaction_to_issue


@pytest.fixture
def reaction_mock_requests_post():
    """Fixture to mock requests.post for GitHub API calls."""
    with patch("services.github.reactions.add_reaction_to_issue.requests.post") as mock:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 123, "content": "+1"}
        mock.return_value = mock_response
        yield mock


@pytest.fixture
def reaction_mock_create_headers():
    """Fixture to mock create_headers utility function."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.create_headers"
    ) as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


@pytest.fixture
def reaction_base_args(create_test_base_args):
    """Fixture providing valid BaseArgs for testing."""
    return create_test_base_args(
        owner="test_owner", repo="test_repo", token="test_token_123"
    )


@pytest.fixture
def reaction_mock_config():
    """Fixture to mock configuration constants."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.GITHUB_API_URL",
        "https://api.github.com",
    ), patch("services.github.reactions.add_reaction_to_issue.TIMEOUT", 120):
        yield


def test_add_reaction_to_issue_success(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test successful reaction addition to an issue."""
    issue_number = 123
    content = "+1"

    result = add_reaction_to_issue(issue_number, content, reaction_base_args)

    # Verify the function returns None as expected
    assert result is None

    # Verify requests.post was called with correct parameters
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )

    # Verify create_headers was called with the token
    reaction_mock_create_headers.assert_called_once_with(token="test_token_123")

    # Verify response methods were called
    reaction_mock_requests_post.return_value.raise_for_status.assert_called_once()
    reaction_mock_requests_post.return_value.json.assert_called_once()


def test_add_reaction_to_issue_different_reactions(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test adding different types of reactions."""
    test_cases = [
        (456, "+1"),
        (789, "-1"),
        (101, "laugh"),
        (202, "confused"),
        (303, "heart"),
        (404, "hooray"),
        (505, "rocket"),
        (606, "eyes"),
    ]

    for issue_number, content in test_cases:
        reaction_mock_requests_post.reset_mock()
        reaction_mock_create_headers.reset_mock()

        result = add_reaction_to_issue(issue_number, content, reaction_base_args)

        assert result is None
        reaction_mock_requests_post.assert_called_once_with(
            url=f"https://api.github.com/repos/test_owner/test_repo/issues/{issue_number}/reactions",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test_token",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"content": content},
            timeout=120,
        )


def test_add_reaction_to_issue_different_repositories(
    reaction_mock_requests_post, reaction_mock_create_headers, create_test_base_args
):
    """Test adding reactions to issues in different repositories."""
    test_cases = [
        create_test_base_args(owner="owner1", repo="repo1", token="token1"),
        create_test_base_args(owner="owner2", repo="repo2", token="token2"),
        create_test_base_args(owner="test-org", repo="test-repo", token="token3"),
        create_test_base_args(owner="user_name", repo="project_name", token="token4"),
    ]

    issue_number = 100
    content = "+1"

    for args in test_cases:
        reaction_mock_requests_post.reset_mock()
        reaction_mock_create_headers.reset_mock()

        result = add_reaction_to_issue(issue_number, content, args)

        assert result is None
        reaction_mock_requests_post.assert_called_once_with(
            url=f"https://api.github.com/repos/{args['owner']}/{args['repo']}/issues/{issue_number}/reactions",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test_token",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"content": content},
            timeout=120,
        )
        reaction_mock_create_headers.assert_called_with(token=args["token"])


def test_add_reaction_to_issue_http_error_handled(reaction_base_args):
    """Test that HTTP errors are handled by the decorator and return None."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_add_reaction_to_issue_request_exception_handled(reaction_base_args):
    """Test that request exceptions are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


def test_add_reaction_to_issue_json_decode_error_handled(reaction_base_args):
    """Test that JSON decode errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Invalid JSON", "", 0
        )
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_add_reaction_to_issue_edge_case_values(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with edge case values."""
    test_cases = [
        (0, "+1"),  # Issue number 0
        (999999, "heart"),  # Large issue number
        (1, ""),  # Empty content
        (42, "custom_reaction"),  # Non-standard reaction content
    ]

    for issue_number, content in test_cases:
        reaction_mock_requests_post.reset_mock()
        reaction_mock_create_headers.reset_mock()

        result = add_reaction_to_issue(issue_number, content, reaction_base_args)

        assert result is None
        reaction_mock_requests_post.assert_called_once_with(
            url=f"https://api.github.com/repos/test_owner/test_repo/issues/{issue_number}/reactions",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test_token",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"content": content},
            timeout=120,
        )


def test_add_reaction_to_issue_response_json_called(
    reaction_mock_requests_post, reaction_base_args
):
    """Test that response.json() is called even though result is not used."""
    result = add_reaction_to_issue(123, "+1", reaction_base_args)

    assert result is None
    reaction_mock_requests_post.return_value.json.assert_called_once()


def test_add_reaction_to_issue_timeout_error_handled(reaction_base_args):
    """Test that timeout errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate timeout error
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


def test_add_reaction_to_issue_rate_limit_403_handled(reaction_base_args):
    """Test that 403 rate limit errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # First response: 403 rate limit error
        mock_response_error = MagicMock()
        mock_response_error.status_code = 403
        mock_response_error.reason = "Forbidden"
        mock_response_error.text = "API rate limit exceeded"
        mock_response_error.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1640995200",
        }

        # Second response: success
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {"id": 1}

        # Configure mock to return error first, then success
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response_error
        mock_response_error.raise_for_status.side_effect = http_error

        mock_post.side_effect = [mock_response_error, mock_response_success]

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # Should succeed after retry
        assert result is None  # Function returns None on success
        assert mock_post.call_count == 2  # Called twice: first fails, second succeeds


def test_add_reaction_to_issue_rate_limit_429_handled(reaction_base_args):
    """Test that 429 rate limit errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate 429 rate limit error
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.reason = "Too Many Requests"
        mock_response.text = "API rate limit exceeded"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1756391658",
        }

        http_error = requests.exceptions.HTTPError("429 Too Many Requests")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_add_reaction_to_issue_secondary_rate_limit_handled(reaction_base_args):
    """Test that secondary rate limit errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate secondary rate limit error
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "You have exceeded a secondary rate limit"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4000",
            "X-RateLimit-Used": "1000",
            "Retry-After": "60",
        }

        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_add_reaction_to_issue_500_error_handled(reaction_base_args):
    """Test that 500 internal server errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate 500 internal server error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Internal server error"

        http_error = requests.exceptions.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_add_reaction_to_issue_401_unauthorized_handled(reaction_base_args):
    """Test that 401 unauthorized errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate 401 unauthorized error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.text = "Bad credentials"

        http_error = requests.exceptions.HTTPError("401 Unauthorized")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_add_reaction_to_issue_422_unprocessable_entity_handled(
    reaction_base_args,
):
    """Test that 422 unprocessable entity errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate 422 unprocessable entity error
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.reason = "Unprocessable Entity"
        mock_response.text = "Validation Failed"

        http_error = requests.exceptions.HTTPError("422 Unprocessable Entity")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_add_reaction_to_issue_ssl_error_handled(reaction_base_args):
    """Test that SSL errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate SSL error
        mock_post.side_effect = requests.exceptions.SSLError(
            "SSL certificate verification failed"
        )

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


def test_add_reaction_to_issue_create_headers_exception_handled(
    reaction_base_args,
):
    """Test that exceptions in create_headers are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.create_headers"
    ) as mock_create_headers:
        # Simulate exception in create_headers
        mock_create_headers.side_effect = Exception("Header creation failed")

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test_token_123")


def test_add_reaction_to_issue_key_error_in_base_args_handled():
    """Test that KeyError from missing base_args keys is handled by the decorator."""
    # Create incomplete base_args missing required keys
    incomplete_base_args = {"owner": "test_owner"}  # Missing repo and token

    result = add_reaction_to_issue(123, "+1", incomplete_base_args)

    # The handle_exceptions decorator should catch the KeyError and return None
    assert result is None


def test_add_reaction_to_issue_attribute_error_handled(reaction_base_args):
    """Test that AttributeError is handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate AttributeError
        mock_post.side_effect = AttributeError(
            "'NoneType' object has no attribute 'post'"
        )

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


def test_add_reaction_to_issue_type_error_handled(reaction_base_args):
    """Test that TypeError is handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate TypeError
        mock_post.side_effect = TypeError("unsupported operand type(s)")

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


def test_add_reaction_to_issue_negative_issue_number(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with negative issue number."""
    issue_number = -1
    content = "+1"

    result = add_reaction_to_issue(issue_number, content, reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/-1/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )


def test_add_reaction_to_issue_special_characters_in_repo_names(
    reaction_mock_requests_post, reaction_mock_create_headers, create_test_base_args
):
    """Test function with special characters in repository names."""
    special_args = create_test_base_args(
        owner="test-owner_123",
        repo="test-repo.name_with-special.chars",
        token="test_token",
    )

    result = add_reaction_to_issue(123, "+1", special_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner_123/test-repo.name_with-special.chars/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )


def test_add_reaction_to_issue_unicode_content(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with unicode characters in content."""
    unicode_content = "🎉"

    result = add_reaction_to_issue(123, unicode_content, reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "🎉"},
        timeout=120,
    )


def test_add_reaction_to_issue_very_long_token(
    reaction_mock_create_headers, create_test_base_args
):
    """Test function with very long token."""
    long_token = "a" * 1000  # Very long token
    long_token_args = create_test_base_args(
        owner="test_owner", repo="test_repo", token=long_token
    )

    result = add_reaction_to_issue(123, "+1", long_token_args)

    assert result is None
    reaction_mock_create_headers.assert_called_once_with(token=long_token)


def test_add_reaction_to_issue_empty_token(
    reaction_mock_create_headers, create_test_base_args
):
    """Test function with empty token."""
    empty_token_args = create_test_base_args(
        owner="test_owner", repo="test_repo", token=""
    )

    result = add_reaction_to_issue(123, "+1", empty_token_args)

    assert result is None
    reaction_mock_create_headers.assert_called_once_with(token="")


def test_add_reaction_to_issue_response_json_returns_different_data(
    reaction_base_args,
):
    """Test that function works correctly when response.json() returns different data."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        # Return different JSON data than expected
        mock_response.json.return_value = {
            "id": 999,
            "content": "heart",
            "user": {"login": "test_user"},
            "created_at": "2023-01-01T00:00:00Z",
        }
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # Function should still return None regardless of response content
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_add_reaction_to_issue_response_json_returns_empty_dict(
    reaction_base_args,
):
    """Test that function works correctly when response.json() returns empty dict."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # Function should still return None regardless of response content
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_add_reaction_to_issue_response_json_returns_none(reaction_base_args):
    """Test that function works correctly when response.json() returns None."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = None
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # Function should still return None regardless of response content
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_add_reaction_to_issue_with_none_base_args():
    """Test that function handles None base_args gracefully."""
    result = add_reaction_to_issue(123, "+1", None)

    # The handle_exceptions decorator should catch the TypeError and return None
    assert result is None


def test_add_reaction_to_issue_with_none_issue_number(reaction_base_args):
    """Test function with None issue number."""
    result = add_reaction_to_issue(None, "+1", reaction_base_args)

    # The handle_exceptions decorator should catch the error and return None
    assert result is None


def test_add_reaction_to_issue_with_none_content(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with None content."""
    result = add_reaction_to_issue(123, None, reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": None},
        timeout=120,
    )


def test_add_reaction_to_issue_with_float_issue_number(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with float issue number (should be converted to int in URL)."""
    result = add_reaction_to_issue(123.5, "+1", reaction_base_args)

    assert result is None
    # Python f-string will convert float to string, so 123.5 becomes "123.5"
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123.5/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )


def test_add_reaction_to_issue_with_string_issue_number(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with string issue number."""
    result = add_reaction_to_issue("123", "+1", reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )


def test_add_reaction_to_issue_with_boolean_content(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with boolean content."""
    result = add_reaction_to_issue(123, True, reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": True},
        timeout=120,
    )


def test_add_reaction_to_issue_with_whitespace_only_content(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with whitespace-only content."""
    whitespace_content = "   \t\n  "

    result = add_reaction_to_issue(123, whitespace_content, reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": whitespace_content},
        timeout=120,
    )


def test_add_reaction_to_issue_with_numeric_string_content(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with numeric string content."""
    result = add_reaction_to_issue(123, "123", reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "123"},
        timeout=120,
    )


def test_add_reaction_to_issue_with_zero_issue_number(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with zero issue number."""
    result = add_reaction_to_issue(0, "+1", reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/0/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )


def test_add_reaction_to_issue_base_args_missing_multiple_keys():
    """Test that function handles base_args missing multiple required keys."""
    incomplete_base_args = {"owner": "test_owner"}  # Missing repo, token, and others

    result = add_reaction_to_issue(123, "+1", incomplete_base_args)

    # The handle_exceptions decorator should catch the KeyError and return None
    assert result is None


def test_add_reaction_to_issue_with_list_content(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with list content (should be serialized by requests)."""
    list_content = ["+1", "heart"]

    result = add_reaction_to_issue(123, list_content, reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": list_content},
        timeout=120,
    )


def test_add_reaction_to_issue_response_json_raises_value_error(
    reaction_base_args,
):
    """Test that ValueError from response.json() is handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON format")
        mock_post.return_value = mock_response

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_add_reaction_to_issue_requests_post_raises_runtime_error(
    reaction_base_args,
):
    """Test that RuntimeError from requests.post is handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate RuntimeError
        mock_post.side_effect = RuntimeError("Unexpected runtime error")

        result = add_reaction_to_issue(123, "+1", reaction_base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


def test_add_reaction_to_issue_with_very_large_issue_number(
    reaction_mock_requests_post, reaction_mock_create_headers, reaction_base_args
):
    """Test function with very large issue number."""
    large_issue_number = 2**63 - 1  # Maximum 64-bit signed integer

    result = add_reaction_to_issue(large_issue_number, "+1", reaction_base_args)

    assert result is None
    reaction_mock_requests_post.assert_called_once_with(
        url=f"https://api.github.com/repos/test_owner/test_repo/issues/{large_issue_number}/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )
