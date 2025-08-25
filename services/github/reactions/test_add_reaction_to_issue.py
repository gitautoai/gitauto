from unittest.mock import patch, MagicMock
import requests
import pytest
from services.github.reactions.add_reaction_to_issue import add_reaction_to_issue
from services.github.types.github_types import BaseArgs


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post for GitHub API calls."""
    with patch("services.github.reactions.add_reaction_to_issue.requests.post") as mock:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 123, "content": "+1"}
        mock.return_value = mock_response
        yield mock


@pytest.fixture
def mock_create_headers():
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
def base_args():
    """Fixture providing valid BaseArgs for testing."""
    return BaseArgs(owner="test_owner", repo="test_repo", token="test_token_123")


@pytest.fixture
def mock_config():
    """Fixture to mock configuration constants."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.GITHUB_API_URL",
        "https://api.github.com",
    ), patch("services.github.reactions.add_reaction_to_issue.TIMEOUT", 120):
        yield


async def test_add_reaction_to_issue_success(
    mock_requests_post, mock_create_headers, base_args, mock_config
):
    """Test successful reaction addition to an issue."""
    issue_number = 123
    content = "+1"

    result = await add_reaction_to_issue(issue_number, content, base_args)

    # Verify the function returns None as expected
    assert result is None

    # Verify requests.post was called with correct parameters
    mock_requests_post.assert_called_once_with(
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
    mock_create_headers.assert_called_once_with(token="test_token_123")

    # Verify response methods were called
    mock_requests_post.return_value.raise_for_status.assert_called_once()
    mock_requests_post.return_value.json.assert_called_once()


async def test_add_reaction_to_issue_different_reactions(
    mock_requests_post, mock_create_headers, base_args, mock_config
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
        mock_requests_post.reset_mock()
        mock_create_headers.reset_mock()

        result = await add_reaction_to_issue(issue_number, content, base_args)

        assert result is None
        mock_requests_post.assert_called_once_with(
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


async def test_add_reaction_to_issue_different_repositories(
    mock_requests_post, mock_create_headers, mock_config
):
    """Test adding reactions to issues in different repositories."""
    test_cases = [
        BaseArgs(owner="owner1", repo="repo1", token="token1"),
        BaseArgs(owner="owner2", repo="repo2", token="token2"),
        BaseArgs(owner="test-org", repo="test-repo", token="token3"),
        BaseArgs(owner="user_name", repo="project_name", token="token4"),
    ]

    issue_number = 100
    content = "+1"

    for args in test_cases:
        mock_requests_post.reset_mock()
        mock_create_headers.reset_mock()

        result = await add_reaction_to_issue(issue_number, content, args)

        assert result is None
        mock_requests_post.assert_called_once_with(
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
        mock_create_headers.assert_called_with(token=args["token"])


async def test_add_reaction_to_issue_http_error_handled(
    mock_create_headers, base_args, mock_config
):
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

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


async def test_add_reaction_to_issue_request_exception_handled(
    mock_create_headers, base_args, mock_config
):
    """Test that request exceptions are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


async def test_add_reaction_to_issue_json_decode_error_handled(
    mock_create_headers, base_args, mock_config
):
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

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


async def test_add_reaction_to_issue_edge_case_values(
    mock_requests_post, mock_create_headers, base_args, mock_config
):
    """Test function with edge case values."""
    test_cases = [
        (0, "+1"),  # Issue number 0
        (999999, "heart"),  # Large issue number
        (1, ""),  # Empty content
        (42, "custom_reaction"),  # Non-standard reaction content
    ]

    for issue_number, content in test_cases:
        mock_requests_post.reset_mock()
        mock_create_headers.reset_mock()

        result = await add_reaction_to_issue(issue_number, content, base_args)

        assert result is None
        mock_requests_post.assert_called_once_with(
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


async def test_add_reaction_to_issue_response_json_called(
    mock_requests_post, mock_create_headers, base_args, mock_config
):
    """Test that response.json() is called even though result is not used."""
    result = await add_reaction_to_issue(123, "+1", base_args)

    assert result is None
    mock_requests_post.return_value.json.assert_called_once()


async def test_add_reaction_to_issue_timeout_error_handled(
    mock_create_headers, base_args, mock_config
):
    """Test that timeout errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate timeout error
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


async def test_add_reaction_to_issue_rate_limit_403_handled(
    mock_create_headers, base_args, mock_config
):
    """Test that 403 rate limit errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate 403 rate limit error
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "API rate limit exceeded"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1640995200",
        }
        
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


async def test_add_reaction_to_issue_rate_limit_429_handled(
    mock_create_headers, base_args, mock_config
):
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
            "X-RateLimit-Reset": "1640995200",
        }
        
        http_error = requests.exceptions.HTTPError("429 Too Many Requests")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


async def test_add_reaction_to_issue_secondary_rate_limit_handled(
    mock_create_headers, base_args, mock_config
):
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

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


async def test_add_reaction_to_issue_500_error_handled(
    mock_create_headers, base_args, mock_config
):
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

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


async def test_add_reaction_to_issue_401_unauthorized_handled(
    mock_create_headers, base_args, mock_config
):
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

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


async def test_add_reaction_to_issue_422_unprocessable_entity_handled(
    mock_create_headers, base_args, mock_config
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

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


async def test_add_reaction_to_issue_ssl_error_handled(
    mock_create_headers, base_args, mock_config
):
    """Test that SSL errors are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate SSL error
        mock_post.side_effect = requests.exceptions.SSLError("SSL certificate verification failed")

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


async def test_add_reaction_to_issue_create_headers_exception_handled(
    base_args, mock_config
):
    """Test that exceptions in create_headers are handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.create_headers"
    ) as mock_create_headers:
        # Simulate exception in create_headers
        mock_create_headers.side_effect = Exception("Header creation failed")

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test_token_123")


async def test_add_reaction_to_issue_key_error_in_base_args_handled(mock_config):
    """Test that KeyError from missing base_args keys is handled by the decorator."""
    # Create incomplete base_args missing required keys
    incomplete_base_args = {"owner": "test_owner"}  # Missing repo and token

    result = await add_reaction_to_issue(123, "+1", incomplete_base_args)

    # The handle_exceptions decorator should catch the KeyError and return None
    assert result is None


async def test_add_reaction_to_issue_attribute_error_handled(
    mock_create_headers, base_args, mock_config
):
    """Test that AttributeError is handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate AttributeError
        mock_post.side_effect = AttributeError("'NoneType' object has no attribute 'post'")

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


async def test_add_reaction_to_issue_type_error_handled(
    mock_create_headers, base_args, mock_config
):
    """Test that TypeError is handled by the decorator."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        # Simulate TypeError
        mock_post.side_effect = TypeError("unsupported operand type(s)")

        result = await add_reaction_to_issue(123, "+1", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_post.assert_called_once()


async def test_add_reaction_to_issue_negative_issue_number(
    mock_requests_post, mock_create_headers, base_args, mock_config
):
    """Test function with negative issue number."""
    issue_number = -1
    content = "+1"

    result = await add_reaction_to_issue(issue_number, content, base_args)

    assert result is None
    mock_requests_post.assert_called_once_with(
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


async def test_add_reaction_to_issue_special_characters_in_repo_names(
    mock_requests_post, mock_create_headers, mock_config
):
    """Test function with special characters in repository names."""
    special_args = BaseArgs(
        owner="test-owner_123", 
        repo="test-repo.name_with-special.chars", 
        token="test_token"
    )
    
    result = await add_reaction_to_issue(123, "+1", special_args)

    assert result is None
    mock_requests_post.assert_called_once_with(
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


async def test_add_reaction_to_issue_unicode_content(
    mock_requests_post, mock_create_headers, base_args, mock_config
):
    """Test function with unicode characters in content."""
    unicode_content = "🎉"
    
    result = await add_reaction_to_issue(123, unicode_content, base_args)

    assert result is None
    mock_requests_post.assert_called_once_with(
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


async def test_add_reaction_to_issue_very_long_token(
    mock_requests_post, mock_create_headers, mock_config
):
    """Test function with very long token."""
    long_token = "a" * 1000  # Very long token
    long_token_args = BaseArgs(
        owner="test_owner", 
        repo="test_repo", 
        token=long_token
    )
    
    result = await add_reaction_to_issue(123, "+1", long_token_args)

    assert result is None
    mock_create_headers.assert_called_once_with(token=long_token)


async def test_add_reaction_to_issue_empty_token(
    mock_requests_post, mock_create_headers, mock_config
):
    """Test function with empty token."""
    empty_token_args = BaseArgs(
        owner="test_owner", 
        repo="test_repo", 
        token=""
    )
    
    result = await add_reaction_to_issue(123, "+1", empty_token_args)

    assert result is None
    mock_create_headers.assert_called_once_with(token="")


async def test_add_reaction_to_issue_response_json_returns_different_data(
    mock_create_headers, base_args, mock_config
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
            "created_at": "2023-01-01T00:00:00Z"
        }
        mock_post.return_value = mock_response

        result = await add_reaction_to_issue(123, "+1", base_args)

        # Function should still return None regardless of response content
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


async def test_add_reaction_to_issue_response_json_returns_empty_dict(
    mock_create_headers, base_args, mock_config
):
    """Test that function works correctly when response.json() returns empty dict."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        result = await add_reaction_to_issue(123, "+1", base_args)

        # Function should still return None regardless of response content
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


async def test_add_reaction_to_issue_response_json_returns_none(
    mock_create_headers, base_args, mock_config
):
    """Test that function works correctly when response.json() returns None."""
    with patch(
        "services.github.reactions.add_reaction_to_issue.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = None
        mock_post.return_value = mock_response

        result = await add_reaction_to_issue(123, "+1", base_args)

        # Function should still return None regardless of response content
        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()