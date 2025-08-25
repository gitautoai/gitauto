from unittest.mock import patch, MagicMock
import pytest
import requests
from requests import HTTPError

from config import TIMEOUT
from services.github.comments.reply_to_comment import reply_to_comment


@pytest.fixture
def mock_base_args():
    """Fixture providing a complete BaseArgs dictionary for testing."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "pull_number": 123,
        "review_id": 456,
    }


@pytest.fixture
def mock_post_response():
    """Fixture providing a mocked successful POST response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "url": "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_create_headers():
    """Fixture providing mocked headers."""
    with patch("services.github.comments.reply_to_comment.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


def test_reply_to_comment_success(
    mock_base_args, mock_post_response, mock_create_headers
):
    """Test successful reply to comment creation."""
    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(mock_base_args, "Test reply body")

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_post.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123/comments/456/replies",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test-token",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"body": "Test reply body"},
            timeout=TIMEOUT,
        )
        mock_post_response.raise_for_status.assert_called_once()
        mock_post_response.json.assert_called_once()


def test_reply_to_comment_with_empty_body(
    mock_base_args, mock_post_response, mock_create_headers
):
    """Test reply to comment with empty body."""
    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(mock_base_args, "")

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        mock_post.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123/comments/456/replies",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test-token",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"body": ""},
            timeout=TIMEOUT,
        )


def test_reply_to_comment_with_multiline_body(
    mock_base_args, mock_post_response, mock_create_headers
):
    """Test reply to comment with multiline body."""
    multiline_body = """This is a multiline comment.

It contains multiple paragraphs.

- And some bullet points
- With various content"""

    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(mock_base_args, multiline_body)

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        mock_post.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123/comments/456/replies",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test-token",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"body": multiline_body},
            timeout=TIMEOUT,
        )


def test_reply_to_comment_with_special_characters(
    mock_base_args, mock_post_response, mock_create_headers
):
    """Test reply to comment with special characters in body."""
    special_body = "Reply with special chars: @user #123 $var & <tag> \"quotes\" 'apostrophes' 中文 🚀"

    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(mock_base_args, special_body)

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        mock_post.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123/comments/456/replies",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test-token",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"body": special_body},
            timeout=TIMEOUT,
        )


def test_reply_to_comment_http_error_handled(mock_base_args, mock_create_headers):
    """Test that HTTP errors are handled by the decorator and return None."""
    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_response = MagicMock()
        # Create a proper HTTPError with a response object
        http_error = HTTPError("404 Not Found")
        http_error.response = MagicMock()
        http_error.response.status_code = 404
        http_error.response.reason = "Not Found"
        http_error.response.text = "Repository not found"
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = reply_to_comment(mock_base_args, "Test body")

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_reply_to_comment_request_exception_handled(
    mock_base_args, mock_create_headers
):
    """Test that request exceptions are handled by the decorator and return None."""
    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        result = reply_to_comment(mock_base_args, "Test body")

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_post.assert_called_once()


def test_reply_to_comment_json_decode_error_handled(
    mock_base_args, mock_create_headers
):
    """Test that JSON decode errors are handled by the decorator and return None."""
    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        result = reply_to_comment(mock_base_args, "Test body")

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_reply_to_comment_url_construction(
    mock_base_args, mock_post_response, mock_create_headers
):
    """Test that the URL is constructed correctly with different parameters."""
    test_cases = [
        {"owner": "owner1", "repo": "repo1", "pull_number": 1, "review_id": 100},
        {
            "owner": "test-org",
            "repo": "my-repo",
            "pull_number": 999,
            "review_id": 12345,
        },
        {"owner": "user", "repo": "project", "pull_number": 42, "review_id": 789},
    ]

    for case in test_cases:
        base_args = {**mock_base_args, **case}
        expected_url = f"https://api.github.com/repos/{case['owner']}/{case['repo']}/pulls/{case['pull_number']}/comments/{case['review_id']}/replies"

        with patch("services.github.comments.reply_to_comment.post") as mock_post:
            mock_post.return_value = mock_post_response

            reply_to_comment(base_args, "Test body")

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["url"] == expected_url


def test_reply_to_comment_different_tokens(
    mock_base_args, mock_post_response, mock_create_headers
):
    """Test that different tokens are passed correctly to create_headers."""
    test_tokens = ["token1", "ghp_abcdef123456", "ghs_xyz789", ""]

    for token in test_tokens:
        base_args = {**mock_base_args, "token": token}

        with patch("services.github.comments.reply_to_comment.post") as mock_post:
            mock_post.return_value = mock_post_response

            reply_to_comment(base_args, "Test body")

            mock_create_headers.assert_called_with(token=token)


def test_reply_to_comment_response_url_extraction(mock_base_args, mock_create_headers):
    """Test that the URL is correctly extracted from different response formats."""
    test_responses = [
        {"url": "https://api.github.com/repos/owner/repo/pulls/comments/123"},
        {"url": "https://github.com/owner/repo/pull/1#issuecomment-456"},
        {"url": "https://api.github.com/repos/test/test/pulls/comments/999", "id": 999},
    ]

    for response_data in test_responses:
        with patch("services.github.comments.reply_to_comment.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = reply_to_comment(mock_base_args, "Test body")

            assert result == response_data["url"]


@pytest.mark.parametrize(
    "pull_number,review_id",
    [
        (1, 1),
        (999999, 888888),
    ],
)
def test_reply_to_comment_various_ids(
    mock_base_args, mock_post_response, mock_create_headers, pull_number, review_id
):
    """Test reply to comment with various pull number and review ID combinations."""
    base_args = {**mock_base_args, "pull_number": pull_number, "review_id": review_id}
    expected_url = f"https://api.github.com/repos/test-owner/test-repo/pulls/{pull_number}/comments/{review_id}/replies"

    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(base_args, "Test body")

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        call_args = mock_post.call_args
        assert call_args[1]["url"] == expected_url


def test_reply_to_comment_with_zero_values_returns_none(
    mock_base_args, mock_create_headers
):
    """Test that zero values are treated as invalid and function returns None."""
    base_args = {**mock_base_args, "pull_number": 0, "review_id": 0}
    
    # Should return None due to handle_exceptions decorator when validation fails
    result = reply_to_comment(base_args, "Test body")
    assert result is None


@pytest.mark.parametrize(
    "body_content",
    [
        "Simple reply",
        "",
        "A" * 1000,  # Long body
        "Line 1\nLine 2\nLine 3",  # Multiline
        "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
        "Unicode: 你好 🌟 ñoël",
    ],
)
def test_reply_to_comment_various_body_content(
    mock_base_args, mock_post_response, mock_create_headers, body_content
):
    """Test reply to comment with various body content formats."""
    with patch("services.github.comments.reply_to_comment.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(mock_base_args, body_content)

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        call_args = mock_post.call_args
        assert call_args[1]["json"]["body"] == body_content


def test_reply_to_comment_missing_required_fields():
    """Test that function handles missing required fields gracefully."""
    incomplete_base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        # Missing pull_number and review_id
    }

    # The function should handle missing fields gracefully due to the decorator
    result = reply_to_comment(incomplete_base_args, "Test body")
    assert result is None


def test_reply_to_comment_with_none_values():
    """Test that function handles None values in base_args gracefully."""
    base_args_with_none = {
        "owner": None,
        "repo": None,
        "token": None,
        "pull_number": None,
        "review_id": None,
    }

    # The function should handle None values gracefully due to the decorator
    result = reply_to_comment(base_args_with_none, "Test body")
    assert result is None


def test_reply_to_comment_with_none_body(mock_base_args, mock_create_headers):
    """Test that function handles None body gracefully."""
    # The function should handle None body gracefully due to the decorator
    result = reply_to_comment(mock_base_args, None)
    assert result is None
