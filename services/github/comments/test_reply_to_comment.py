# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, MagicMock

import pytest
import requests

from config import TIMEOUT
from services.github.comments.reply_to_comment import reply_to_comment


@pytest.fixture
def mock_post_response():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "url": "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_create_headers():
    with patch("services.github.comments.reply_to_comment.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


def test_reply_to_comment_success(
    mock_post_response, mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(base_args, "Test reply body")

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
    mock_post_response, mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(base_args, "")

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
    mock_post_response, mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    multiline_body = """This is a multiline comment.

It contains multiple paragraphs.

- And some bullet points
- With various content"""

    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(base_args, multiline_body)

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
    mock_post_response, mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    special_body = "Reply with special chars: @user #123 $var & <tag> \"quotes\" 'apostrophes' 中文 🚀"

    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(base_args, special_body)

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


def test_reply_to_comment_http_error_handled(
    mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_response = MagicMock()
        # status_code != 404 so the new 404-skip branch doesn't fire — we want this test to exercise raise_for_status. handle_http_error short-circuits 5xx via is_server_error (returns default without retry).
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = MagicMock()
        http_error.response.status_code = 500
        http_error.response.reason = "Internal Server Error"
        http_error.response.text = "Server error"
        http_error.response.headers = {}
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = reply_to_comment(base_args, "Test body")

        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_reply_to_comment_skips_on_404_without_raising(
    mock_create_headers, create_test_base_args
):
    """Sentry AGENT-303/304 (Foxquilt/foxden-shared-lib PR 629 comment 3093714165): the parent review comment was deleted before GitAuto could reply, GitHub returned 404, raise_for_status raised HTTPError. Old behavior: HTTPError propagated to @handle_exceptions and surfaced to Sentry as a 'real' error every time a thread got cleaned up. New behavior: detect status_code==404 and return None silently — there's nothing to retry and the Sentry alert was just noise."""
    base_args = create_test_base_args(
        owner="Foxquilt",
        repo="foxden-shared-lib",
        token="test-token",
        pr_number=629,
        review_id=3093714165,
    )
    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 404
        # If we mistakenly fall through to raise_for_status, this side_effect proves it — but the new branch returns before reaching it.
        mock_response.raise_for_status.side_effect = AssertionError(
            "raise_for_status should not run when status_code==404"
        )
        mock_post.return_value = mock_response

        result = reply_to_comment(base_args, "Test reply")

        assert result is None
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_not_called()


def test_reply_to_comment_request_exception_handled(
    mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        result = reply_to_comment(base_args, "Test body")

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_post.assert_called_once()


def test_reply_to_comment_json_decode_error_handled(
    mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        result = reply_to_comment(base_args, "Test body")

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_reply_to_comment_url_construction(
    mock_post_response, mock_create_headers, create_test_base_args
):
    test_cases = [
        {"owner": "owner1", "repo": "repo1", "pr_number": 1, "review_id": 100},
        {
            "owner": "test-org",
            "repo": "my-repo",
            "pr_number": 999,
            "review_id": 12345,
        },
        {"owner": "user", "repo": "project", "pr_number": 42, "review_id": 789},
    ]

    for case in test_cases:
        base_args = create_test_base_args(
            token="test-token",
            **case,
        )
        expected_url = f"https://api.github.com/repos/{case['owner']}/{case['repo']}/pulls/{case['pr_number']}/comments/{case['review_id']}/replies"

        with patch(
            "services.github.comments.reply_to_comment.requests.post"
        ) as mock_post:
            mock_post.return_value = mock_post_response

            reply_to_comment(base_args, "Test body")

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["url"] == expected_url


def test_reply_to_comment_different_tokens(
    mock_post_response, mock_create_headers, create_test_base_args
):
    test_tokens = ["token1", "ghp_abcdef123456", "ghs_xyz789", ""]

    for token in test_tokens:
        base_args = create_test_base_args(
            owner="test-owner",
            repo="test-repo",
            token=token,
            pr_number=123,
            review_id=456,
        )

        with patch(
            "services.github.comments.reply_to_comment.requests.post"
        ) as mock_post:
            mock_post.return_value = mock_post_response

            reply_to_comment(base_args, "Test body")

            mock_create_headers.assert_called_with(token=token)


def test_reply_to_comment_response_url_extraction(
    mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    test_responses = [
        {"url": "https://api.github.com/repos/owner/repo/pulls/comments/123"},
        {"url": "https://github.com/owner/repo/pull/1#issuecomment-456"},
        {"url": "https://api.github.com/repos/test/test/pulls/comments/999", "id": 999},
    ]

    for response_data in test_responses:
        with patch(
            "services.github.comments.reply_to_comment.requests.post"
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = reply_to_comment(base_args, "Test body")

            assert result == response_data["url"]


@pytest.mark.parametrize(
    "pr_number,review_id",
    [
        (1, 1),
        (999999, 888888),
    ],
)
def test_reply_to_comment_various_ids(
    mock_post_response, mock_create_headers, pr_number, review_id, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=pr_number,
        review_id=review_id,
    )
    expected_url = f"https://api.github.com/repos/test-owner/test-repo/pulls/{pr_number}/comments/{review_id}/replies"

    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(base_args, "Test body")

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        call_args = mock_post.call_args
        assert call_args[1]["url"] == expected_url


def test_reply_to_comment_with_zero_values_returns_none(
    mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=0,
        review_id=0,
    )

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
    mock_post_response, mock_create_headers, body_content, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        result = reply_to_comment(base_args, body_content)

        assert (
            result
            == "https://api.github.com/repos/test-owner/test-repo/pulls/comments/789"
        )
        call_args = mock_post.call_args
        assert call_args[1]["json"]["body"] == body_content


def test_reply_to_comment_missing_required_fields():
    incomplete_base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
    }

    # Intentionally passing incomplete BaseArgs to test runtime error handling
    result = reply_to_comment(
        incomplete_base_args, "Test body"  # pyright: ignore[reportArgumentType]
    )
    assert result is None


def test_reply_to_comment_with_none_values():
    base_args_with_none = {
        "owner": None,
        "repo": None,
        "token": None,
        "pr_number": None,
        "review_id": None,
    }

    # Intentionally passing None values to test runtime error handling
    result = reply_to_comment(
        base_args_with_none, "Test body"  # pyright: ignore[reportArgumentType]
    )
    assert result is None


def test_reply_to_comment_with_none_body(mock_create_headers, create_test_base_args):
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        pr_number=123,
        review_id=456,
    )
    # Intentionally passing None body to test runtime error handling
    result = reply_to_comment(base_args, None)  # pyright: ignore[reportArgumentType]
    assert result is None


def test_pr_review_uses_issue_comments_api(mock_post_response, mock_create_headers):
    base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "pr_number": 123,
        "review_subject_type": "pr_review",
    }

    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        # Intentionally passing partial dict to test runtime behavior
        reply_to_comment(
            base_args, "PR-level reply"  # pyright: ignore[reportArgumentType]
        )

        mock_post.assert_called_once()
        call_url = mock_post.call_args[1]["url"]
        assert (
            call_url
            == "https://api.github.com/repos/test-owner/test-repo/issues/123/comments"
        )


def test_pr_comment_uses_issue_comments_api(mock_post_response, mock_create_headers):
    base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "pr_number": 123,
        "review_id": 789,
        "review_subject_type": "pr_comment",
    }

    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        # Intentionally passing partial dict to test runtime behavior
        reply_to_comment(
            base_args, "PR comment reply"  # pyright: ignore[reportArgumentType]
        )

        mock_post.assert_called_once()
        call_url = mock_post.call_args[1]["url"]
        assert (
            call_url
            == "https://api.github.com/repos/test-owner/test-repo/issues/123/comments"
        )


def test_inline_review_without_review_id_returns_none(mock_create_headers):
    base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "pr_number": 123,
        "review_subject_type": "line",
        # No review_id
    }

    # Intentionally passing partial dict to test runtime behavior
    result = reply_to_comment(
        base_args, "Test body"  # pyright: ignore[reportArgumentType]
    )
    assert result is None


def test_inline_review_with_review_id_uses_replies_api(
    mock_post_response, mock_create_headers
):
    base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "pr_number": 123,
        "review_id": 456,
        "review_subject_type": "line",
    }

    with patch("services.github.comments.reply_to_comment.requests.post") as mock_post:
        mock_post.return_value = mock_post_response

        # Intentionally passing partial dict to test runtime behavior
        reply_to_comment(
            base_args, "Inline reply"  # pyright: ignore[reportArgumentType]
        )

        mock_post.assert_called_once()
        call_url = mock_post.call_args[1]["url"]
        assert (
            call_url
            == "https://api.github.com/repos/test-owner/test-repo/pulls/123/comments/456/replies"
        )
