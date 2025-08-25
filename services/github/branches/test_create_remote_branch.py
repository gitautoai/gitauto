from unittest.mock import patch, MagicMock
import pytest
import requests

from services.github.branches.create_remote_branch import create_remote_branch
from test_utils import create_test_base_args


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post for successful API calls."""
    with patch(
        "services.github.branches.create_remote_branch.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch(
        "services.github.branches.create_remote_branch.create_headers"
    ) as mock_headers:
        mock_headers.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock_headers


@pytest.fixture
def sample_base_args():
    """Fixture providing sample BaseArgs for testing."""
    return create_test_base_args()


@pytest.fixture
def sample_sha():
    """Fixture providing a sample SHA for testing."""
    return "abc123def456789"


def test_create_remote_branch_success(
    mock_requests_post, mock_create_headers, sample_base_args, sample_sha
):
    """Test successful creation of a remote branch."""
    result = create_remote_branch(sha=sample_sha, base_args=sample_base_args)

    # Verify the function returns None on success
    assert result is None

    # Verify requests.post was called with correct parameters
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/git/refs",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"ref": "refs/heads/feature/test-branch", "sha": "abc123def456789"},
        timeout=120,
    )

    # Verify create_headers was called with the token
    mock_create_headers.assert_called_once_with(token="test_token_123")

    # Verify raise_for_status was called
    mock_requests_post.return_value.raise_for_status.assert_called_once()


def test_create_remote_branch_with_different_branch_names(
    mock_requests_post, mock_create_headers, sample_sha
):
    """Test branch creation with various branch name formats."""
    test_cases = [
        "main",
        "develop",
        "feature/new-feature",
        "bugfix/fix-123",
        "hotfix/urgent-fix",
        "release/v1.0.0",
        "feature_branch_with_underscores",
        "branch-with-dashes",
        "123-numeric-start",
        "UPPERCASE-BRANCH",
    ]

    for branch_name in test_cases:
        mock_requests_post.reset_mock()
        mock_create_headers.reset_mock()

        base_args = create_test_base_args(
            owner="test_owner",
            repo="test_repo",
            new_branch=branch_name,
            token="test_token",
        )

        result = create_remote_branch(sha=sample_sha, base_args=base_args)
        assert result is None

        # Verify the ref format is correct
        call_args = mock_requests_post.call_args
        expected_ref = f"refs/heads/{branch_name}"
        assert call_args[1]["json"]["ref"] == expected_ref


def test_create_remote_branch_with_different_shas(
    mock_requests_post, mock_create_headers, sample_base_args
):
    """Test branch creation with various SHA formats."""
    test_shas = [
        "abc123",
        "1234567890abcdef",
        "a1b2c3d4e5f6789012345678901234567890abcd",
        "0123456789abcdef0123456789abcdef01234567",
        "f" * 40,  # 40 character SHA
    ]

    for sha in test_shas:
        mock_requests_post.reset_mock()
        mock_create_headers.reset_mock()

        result = create_remote_branch(sha=sha, base_args=sample_base_args)
        assert result is None

        # Verify the SHA is passed correctly
        call_args = mock_requests_post.call_args
        assert call_args[1]["json"]["sha"] == sha


def test_create_remote_branch_http_error_raised(
    mock_create_headers, sample_base_args, sample_sha
):
    """Test that HTTP errors are raised due to raise_on_error=True."""
    with patch(
        "services.github.branches.create_remote_branch.requests.post"
    ) as mock_post:
        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Repository not found"

        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        # The function should raise HTTPError due to raise_on_error=True
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            create_remote_branch(sha=sample_sha, base_args=sample_base_args)

        assert str(exc_info.value) == "404 Not Found"

        # Verify the request was still made
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_create_remote_branch_request_timeout_raised(
    mock_create_headers, sample_base_args, sample_sha
):
    """Test that request timeout is raised due to raise_on_error=True."""
    with patch(
        "services.github.branches.create_remote_branch.requests.post"
    ) as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        # The function should raise Timeout due to raise_on_error=True
        with pytest.raises(requests.exceptions.Timeout) as exc_info:
            create_remote_branch(sha=sample_sha, base_args=sample_base_args)

        assert str(exc_info.value) == "Request timed out"

        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_remote_branch_connection_error_raised(
    mock_create_headers, sample_base_args, sample_sha
):
    """Test that connection errors are raised due to raise_on_error=True."""
    with patch(
        "services.github.branches.create_remote_branch.requests.post"
    ) as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # The function should raise ConnectionError due to raise_on_error=True
        with pytest.raises(requests.exceptions.ConnectionError) as exc_info:
            create_remote_branch(sha=sample_sha, base_args=sample_base_args)

        assert str(exc_info.value) == "Connection failed"

        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_remote_branch_uses_correct_api_url(
    mock_requests_post, mock_create_headers, sample_base_args, sample_sha
):
    """Test that the correct GitHub API URL is used."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)

    call_args = mock_requests_post.call_args
    expected_url = "https://api.github.com/repos/test_owner/test_repo/git/refs"
    assert call_args[1]["url"] == expected_url


def test_create_remote_branch_uses_correct_timeout(
    mock_requests_post, mock_create_headers, sample_base_args, sample_sha
):
    """Test that the correct timeout value is used."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)

    call_args = mock_requests_post.call_args
    assert call_args[1]["timeout"] == 120


def test_create_remote_branch_json_payload_structure(
    mock_requests_post, mock_create_headers, sample_base_args, sample_sha
):
    """Test that the JSON payload has the correct structure."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)

    call_args = mock_requests_post.call_args
    json_payload = call_args[1]["json"]

    # Verify payload structure
    assert "ref" in json_payload
    assert "sha" in json_payload
    assert len(json_payload) == 2

    # Verify payload values
    assert json_payload["ref"] == "refs/heads/feature/test-branch"
    assert json_payload["sha"] == sample_sha


def test_create_remote_branch_with_special_characters_in_owner_repo(
    mock_requests_post, mock_create_headers, sample_sha
):
    """Test branch creation with special characters in owner and repo names."""
    base_args = create_test_base_args(
        owner="test-owner_123",
        repo="test.repo-name_456",
        new_branch="feature/test",
        token="test_token",
    )

    result = create_remote_branch(sha=sample_sha, base_args=base_args)
    assert result is None

    call_args = mock_requests_post.call_args
    expected_url = (
        "https://api.github.com/repos/test-owner_123/test.repo-name_456/git/refs"
    )
    assert call_args[1]["url"] == expected_url


def test_create_remote_branch_extracts_base_args_correctly(
    mock_requests_post, mock_create_headers, sample_sha
):
    """Test that BaseArgs values are extracted correctly."""
    base_args = create_test_base_args(
        owner="extracted_owner",
        repo="extracted_repo",
        new_branch="extracted/branch",
        token="extracted_token",
        # Include other fields that should be ignored
        issue_number=123,
        sender_name="test_sender",
    )

    create_remote_branch(sha=sample_sha, base_args=base_args)

    # Verify only the required fields were used
    call_args = mock_requests_post.call_args
    assert "extracted_owner" in call_args[1]["url"]
    assert "extracted_repo" in call_args[1]["url"]
    assert call_args[1]["json"]["ref"] == "refs/heads/extracted/branch"

    # Verify create_headers was called with the extracted token
    mock_create_headers.assert_called_once_with(token="extracted_token")


def test_create_remote_branch_with_monkeypatch(
    monkeypatch, sample_base_args, sample_sha
):
    """Test using monkeypatch for configuration values."""
    # Mock configuration values
    monkeypatch.setattr(
        "services.github.branches.create_remote_branch.GITHUB_API_URL",
        "https://test.api.github.com",
    )
    monkeypatch.setattr("services.github.branches.create_remote_branch.TIMEOUT", 60)

    with patch(
        "services.github.branches.create_remote_branch.requests.post"
    ) as mock_post, patch(
        "services.github.branches.create_remote_branch.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test"}

        result = create_remote_branch(sha=sample_sha, base_args=sample_base_args)
        assert result is None

        # Verify the mocked URL and timeout were used
        call_args = mock_post.call_args
        assert "https://test.api.github.com" in call_args[1]["url"]
        assert call_args[1]["timeout"] == 60


def test_create_remote_branch_with_empty_values(
    mock_requests_post, mock_create_headers
):
    """Test behavior with empty or minimal values."""
    base_args = create_test_base_args(owner="", repo="", new_branch="", token="")

    result = create_remote_branch(sha="", base_args=base_args)
    assert result is None

    # Verify the function still makes the request even with empty values
    mock_requests_post.assert_called_once()
    call_args = mock_requests_post.call_args
    assert call_args[1]["json"]["ref"] == "refs/heads/"
    assert call_args[1]["json"]["sha"] == ""


@pytest.mark.parametrize(
    "error_type,error_message",
    [
        (requests.exceptions.Timeout, "Timeout Error"),
        (requests.exceptions.ConnectionError, "Connection Error"),
        (requests.exceptions.RequestException, "Request Error"),
        (ValueError, "Value Error"),
        (KeyError, "Key Error"),
    ],
)
def test_create_remote_branch_raises_various_exceptions(
    mock_create_headers, sample_base_args, sample_sha, error_type, error_message
):
    """Test that various exception types are raised due to raise_on_error=True."""
    with patch(
        "services.github.branches.create_remote_branch.requests.post"
    ) as mock_post:
        mock_post.side_effect = error_type(error_message)

        # The function should raise the exception due to raise_on_error=True
        with pytest.raises(error_type) as exc_info:
            create_remote_branch(sha=sample_sha, base_args=sample_base_args)

        # KeyError adds quotes around the message, other exceptions don't
        if error_type is KeyError:
            assert str(exc_info.value) == f"'{error_message}'"
        else:
            assert str(exc_info.value) == error_message

        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_remote_branch_raises_http_error_exception(
    mock_create_headers, sample_base_args, sample_sha
):
    """Test that HTTPError is raised due to raise_on_error=True with proper response object."""
    with patch(
        "services.github.branches.create_remote_branch.requests.post"
    ) as mock_post:
        # Create a proper HTTPError with response object
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "HTTP Error"
        http_error = requests.exceptions.HTTPError("HTTP Error")
        http_error.response = mock_response
        mock_post.side_effect = http_error

        # The function should raise HTTPError due to raise_on_error=True
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            create_remote_branch(sha=sample_sha, base_args=sample_base_args)

        assert str(exc_info.value) == "HTTP Error"

        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_remote_branch_ref_format_consistency(
    mock_requests_post, mock_create_headers, sample_sha
):
    """Test that the ref format is consistently 'refs/heads/{branch_name}'."""
    test_branches = [
        ("simple", "refs/heads/simple"),
        ("feature/complex-branch", "refs/heads/feature/complex-branch"),
        ("123-numeric", "refs/heads/123-numeric"),
        ("CAPS_AND_underscores", "refs/heads/CAPS_AND_underscores"),
    ]

    for branch_name, expected_ref in test_branches:
        mock_requests_post.reset_mock()

        base_args = create_test_base_args(
            owner="test_owner",
            repo="test_repo",
            new_branch=branch_name,
            token="test_token",
        )

        create_remote_branch(sha=sample_sha, base_args=base_args)

        call_args = mock_requests_post.call_args
        assert call_args[1]["json"]["ref"] == expected_ref


def test_create_remote_branch_api_endpoint_structure(
    mock_requests_post, mock_create_headers, sample_base_args, sample_sha
):
    """Test that the API endpoint follows GitHub's expected structure."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)

    call_args = mock_requests_post.call_args
    url = call_args[1]["url"]

    # Verify URL structure matches GitHub API pattern
    assert url.startswith("https://api.github.com/repos/")
    assert url.endswith("/git/refs")
    assert "/test_owner/test_repo/" in url


def test_create_remote_branch_request_method_and_headers(
    mock_requests_post, mock_create_headers, sample_base_args, sample_sha
):
    """Test that the correct HTTP method and headers are used."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)

    # Verify POST method was used (implicit in requests.post call)
    mock_requests_post.assert_called_once()

    # Verify headers were set correctly
    call_args = mock_requests_post.call_args
    assert "headers" in call_args[1]

    # Verify create_headers was called
    mock_create_headers.assert_called_once_with(token="test_token_123")
