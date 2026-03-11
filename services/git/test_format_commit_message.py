# Standard imports
from typing import cast
from unittest.mock import patch

# Local imports
from services.git.format_commit_message import format_commit_message
from services.types.base_args import BaseArgs


def _make_base_args(
    sender_email: str | None = "user@example.com",
    sender_display_name: str = "Test User",
    sender_id: int = 12345,
    sender_name: str = "testuser",
    reviewers: list[str] | None = None,
):
    return cast(
        BaseArgs,
        {
            "sender_email": sender_email,
            "sender_display_name": sender_display_name,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "reviewers": reviewers or [],
        },
    )


def test_with_email():
    base_args = _make_base_args(sender_email="user@example.com")
    result = format_commit_message(message="Update README.md", base_args=base_args)
    assert result == "Update README.md\n\nCo-Authored-By: Test User <user@example.com>"


def test_with_email_none_uses_noreply_fallback():
    base_args = _make_base_args(sender_email=None)
    result = format_commit_message(message="Create file.py", base_args=base_args)
    assert (
        result
        == "Create file.py\n\nCo-Authored-By: Test User <12345+testuser@users.noreply.github.com>"
    )


def test_preserves_original_message():
    base_args = _make_base_args()
    result = format_commit_message(
        message="Fix bug in parser [skip ci]", base_args=base_args
    )
    assert result.startswith("Fix bug in parser [skip ci]\n\n")
    assert "Co-Authored-By:" in result


@patch("services.git.format_commit_message.GITHUB_APP_USER_ID", new=99999)
def test_bot_sender_credits_all_reviewers():
    base_args = _make_base_args(sender_id=99999, reviewers=["alice", "bob"])
    result = format_commit_message(message="Update file.py", base_args=base_args)
    assert result == (
        "Update file.py\n\n"
        "Co-Authored-By: alice <alice@users.noreply.github.com>\n"
        "Co-Authored-By: bob <bob@users.noreply.github.com>"
    )


@patch("services.git.format_commit_message.GITHUB_APP_USER_ID", new=99999)
def test_bot_sender_no_reviewers_skips_co_author():
    base_args = _make_base_args(sender_id=99999, reviewers=[])
    result = format_commit_message(message="Initial commit", base_args=base_args)
    assert result == "Initial commit"
    assert "Co-Authored-By" not in result
