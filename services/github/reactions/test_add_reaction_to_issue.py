from unittest.mock import patch, MagicMock
import pytest
import requests
from services.github.reactions.add_reaction_to_issue import add_reaction_to_issue
from services.github.types.github_types import BaseArgs


@pytest.fixture
def base_args():
    """Fixture providing basic BaseArgs for testing."""
    return BaseArgs(
        input_from="github",
        owner_type="Organization",
        owner_id=123456,
        owner="test-owner",
        repo_id=789012,
        repo="test-repo",
        clone_url="https://github.com/test-owner/test-repo.git",
        is_fork=False,
        issue_number=1,
        issue_title="Test Issue",
        issue_body="Test issue body",
        issue_comments=[],
        latest_commit_sha="abc123",
        issuer_name="test-user",
        base_branch="main",
        new_branch="feature-branch",
        installation_id=12345,
        token="test-token",
        sender_id=67890,
        sender_name="test-sender",
        sender_email="test@example.com",
        is_automation=False,
        reviewers=[],
        github_urls=[],
        other_urls=[],
    )


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post method."""
    with patch("services.github.reactions.add_reaction_to_issue.requests.post") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.reactions.add_reaction_to_issue.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


@pytest.fixture
def mock_successful_response():
    """Fixture providing a successful HTTP response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 12345,
        "content": "+1",
        "user": {"login": "test-user"},
        "created_at": "2024-01-01T00:00:00Z",
    }
    return mock_response


def test_add_reaction_to_issue_success(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test successful reaction addition to an issue."""
    # Setup
    mock_requests_post.return_value = mock_successful_response
    issue_number = 123
    content = "+1"

    # Execute
    result = add_reaction_to_issue(issue_number, content, base_args)

    # Assert
    assert result is None  # Function returns None on success
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/issues/123/reactions",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"content": "+1"},
        timeout=120,
    )
    mock_successful_response.raise_for_status.assert_called_once()
    mock_successful_response.json.assert_called_once()


def test_add_reaction_to_issue_different_reactions(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test adding different types of reactions."""
    mock_requests_post.return_value = mock_successful_response
    reactions = ["+1", "-1", "laugh", "confused", "heart", "hooray", "rocket", "eyes"]

    for reaction in reactions:
        # Execute
        result = add_reaction_to_issue(456, reaction, base_args)

        # Assert
        assert result is None
        # Verify the reaction content was passed correctly
        call_args = mock_requests_post.call_args
        assert call_args[1]["json"]["content"] == reaction


def test_add_reaction_to_issue_different_issue_numbers(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test adding reactions to different issue numbers."""
    mock_requests_post.return_value = mock_successful_response
    issue_numbers = [1, 100, 999, 12345]

    for issue_num in issue_numbers:
        # Execute
        result = add_reaction_to_issue(issue_num, "+1", base_args)

        # Assert
        assert result is None
        # Verify the URL contains the correct issue number
        call_args = mock_requests_post.call_args
        expected_url = f"https://api.github.com/repos/test-owner/test-repo/issues/{issue_num}/reactions"
        assert call_args[1]["url"] == expected_url


def test_add_reaction_to_issue_different_repositories(
    mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test adding reactions to issues in different repositories."""
    mock_requests_post.return_value = mock_successful_response
    
    repos = [
        ("owner1", "repo1"),
        ("owner2", "repo2"),
        ("test-org", "test-project"),
    ]

    for owner, repo in repos:
        # Create base_args for each repo
        test_base_args = BaseArgs(
            input_from="github",
            owner_type="Organization",
            owner_id=123456,
            owner=owner,
            repo_id=789012,
            repo=repo,
            clone_url=f"https://github.com/{owner}/{repo}.git",
            is_fork=False,
            issue_number=1,
            issue_title="Test Issue",
            issue_body="Test issue body",
            issue_comments=[],
            latest_commit_sha="abc123",
            issuer_name="test-user",
            base_branch="main",
            new_branch="feature-branch",
            installation_id=12345,
            token="test-token",
            sender_id=67890,
            sender_name="test-sender",
            sender_email="test@example.com",
            is_automation=False,
            reviewers=[],
            github_urls=[],
            other_urls=[],
        )

        # Execute
        result = add_reaction_to_issue(123, "+1", test_base_args)

        # Assert
        assert result is None
        # Verify the URL contains the correct owner and repo
        call_args = mock_requests_post.call_args
        expected_url = f"https://api.github.com/repos/{owner}/{repo}/issues/123/reactions"
        assert call_args[1]["url"] == expected_url


def test_add_reaction_to_issue_http_error(
    base_args, mock_requests_post, mock_create_headers
):
    """Test handling of HTTP errors during reaction addition."""
    # Setup
    mock_response = MagicMock()
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Not Found"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found", response=mock_error_response)
    mock_requests_post.return_value = mock_response

    # Execute
    result = add_reaction_to_issue(123, "+1", base_args)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_add_reaction_to_issue_network_error(
    base_args, mock_requests_post, mock_create_headers
):
    """Test handling of network errors during reaction addition."""
    # Setup
    mock_requests_post.side_effect = requests.exceptions.ConnectionError("Network error")

    # Execute
    result = add_reaction_to_issue(123, "+1", base_args)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()


def test_add_reaction_to_issue_json_decode_error(
    base_args, mock_requests_post, mock_create_headers
):
    """Test handling of JSON decode errors."""
    # Setup
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_post.return_value = mock_response

    # Execute
    result = add_reaction_to_issue(123, "+1", base_args)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_add_reaction_to_issue_empty_content(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test adding reaction with empty content."""
    # Setup
    mock_requests_post.return_value = mock_successful_response

    # Execute
    result = add_reaction_to_issue(123, "", base_args)

    # Assert
    assert result is None
    call_args = mock_requests_post.call_args
    assert call_args[1]["json"]["content"] == ""


def test_add_reaction_to_issue_special_characters_content(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test adding reaction with special characters in content."""
    # Setup
    mock_requests_post.return_value = mock_successful_response
    special_content = "special-chars-123!@#"

    # Execute
    result = add_reaction_to_issue(123, special_content, base_args)

    # Assert
    assert result is None
    call_args = mock_requests_post.call_args
    assert call_args[1]["json"]["content"] == special_content


def test_add_reaction_to_issue_timeout_configuration(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test that the correct timeout value is used."""
    # Setup
    mock_requests_post.return_value = mock_successful_response

    # Execute
    result = add_reaction_to_issue(123, "+1", base_args)

    # Assert
    assert result is None
    call_args = mock_requests_post.call_args
    assert call_args[1]["timeout"] == 120  # TIMEOUT from config


def test_add_reaction_to_issue_url_construction(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test that the GitHub API URL is constructed correctly."""
    # Setup
    mock_requests_post.return_value = mock_successful_response

    # Execute
    result = add_reaction_to_issue(999, "heart", base_args)

    # Assert
    assert result is None
    call_args = mock_requests_post.call_args
    expected_url = "https://api.github.com/repos/test-owner/test-repo/issues/999/reactions"
    assert call_args[1]["url"] == expected_url


def test_add_reaction_to_issue_json_payload_structure(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test that the JSON payload is structured correctly."""
    # Setup
    mock_requests_post.return_value = mock_successful_response

    # Execute
    result = add_reaction_to_issue(123, "rocket", base_args)

    # Assert
    assert result is None
    call_args = mock_requests_post.call_args
    json_payload = call_args[1]["json"]
    assert isinstance(json_payload, dict)
    assert len(json_payload) == 1
    assert "content" in json_payload
    assert json_payload["content"] == "rocket"


def test_add_reaction_to_issue_headers_passed_correctly(
    base_args, mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test that headers are passed correctly to the request."""
    # Setup
    expected_headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test-token",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    mock_create_headers.return_value = expected_headers
    mock_requests_post.return_value = mock_successful_response

    # Execute
    result = add_reaction_to_issue(123, "+1", base_args)

    # Assert
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    call_args = mock_requests_post.call_args
    assert call_args[1]["headers"] == expected_headers


def test_add_reaction_to_issue_response_processing(
    base_args, mock_requests_post, mock_create_headers
):
    """Test that response is processed correctly."""
    # Setup
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"id": 54321, "content": "eyes"}
    mock_requests_post.return_value = mock_response

    # Execute
    result = add_reaction_to_issue(123, "eyes", base_args)

    # Assert
    assert result is None
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_add_reaction_to_issue_base_args_extraction(
    mock_requests_post, mock_create_headers, mock_successful_response
):
    """Test that owner, repo, and token are correctly extracted from base_args."""
    # Setup
    mock_requests_post.return_value = mock_successful_response
    custom_base_args = BaseArgs(
        input_from="github",
        owner_type="User",
        owner_id=999999,
        owner="custom-owner",
        repo_id=888888,
        repo="custom-repo",
        clone_url="https://github.com/custom-owner/custom-repo.git",
        is_fork=True,
        issue_number=42,
        issue_title="Custom Issue",
        issue_body="Custom issue body",
        issue_comments=["comment1"],
        latest_commit_sha="xyz789",
        issuer_name="custom-user",
        base_branch="develop",
        new_branch="custom-branch",
        installation_id=54321,
        token="custom-token",
        sender_id=11111,
        sender_name="custom-sender",
        sender_email="custom@example.com",
        is_automation=True,
        reviewers=["reviewer1"],
        github_urls=["url1"],
        other_urls=["url2"],
    )

    # Execute
    result = add_reaction_to_issue(789, "confused", custom_base_args)

    # Assert
    assert result is None
    mock_create_headers.assert_called_once_with(token="custom-token")
    call_args = mock_requests_post.call_args
    expected_url = "https://api.github.com/repos/custom-owner/custom-repo/issues/789/reactions"
    assert call_args[1]["url"] == expected_url
