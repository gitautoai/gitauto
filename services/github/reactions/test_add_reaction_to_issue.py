from unittest.mock import patch, MagicMock
import requests
import pytest
from services.github.reactions.add_reaction_to_issue import add_reaction_to_issue
from test_utils import create_test_base_args


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
    return create_test_base_args(
        owner="test_owner", repo="test_repo", token="test_token_123"
    )


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
        create_test_base_args(owner="owner1", repo="repo1", token="token1"),
        create_test_base_args(owner="owner2", repo="repo2", token="token2"),
        create_test_base_args(owner="test-org", repo="test-repo", token="token3"),
        create_test_base_args(owner="user_name", repo="project_name", token="token4"),
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
