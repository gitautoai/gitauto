from unittest.mock import MagicMock, patch

from services.git.get_branch_head_author import get_branch_head_author


def test_returns_author_string_on_success():
    def fake_run(args, cwd):  # pylint: disable=unused-argument
        if args[:2] == ["git", "fetch"]:
            return MagicMock(returncode=0, stdout="", stderr="")
        if args[:2] == ["git", "log"]:
            return MagicMock(
                returncode=0, stdout="Alice <alice@example.com>\n", stderr=""
            )
        raise AssertionError(f"unexpected call: {args}")

    with patch(
        "services.git.get_branch_head_author.run_subprocess", side_effect=fake_run
    ):
        result = get_branch_head_author(
            "/tmp/repo", "https://x-access-token:tok@github.com/o/r.git", "main"
        )

    assert result == "Alice <alice@example.com>"


def test_returns_unknown_when_fetch_fails():
    """If the helper can't reach the remote, return "unknown" so callers can still log something and keep going."""

    def fake_run(args, cwd):  # pylint: disable=unused-argument
        if args[:2] == ["git", "fetch"]:
            raise ValueError("Command failed: fatal: unable to access")
        raise AssertionError("log should not be reached")

    with patch(
        "services.git.get_branch_head_author.run_subprocess", side_effect=fake_run
    ):
        result = get_branch_head_author(
            "/tmp/repo", "https://x-access-token:tok@github.com/o/r.git", "main"
        )

    assert result == "unknown"


def test_returns_unknown_when_log_fails():
    def fake_run(args, cwd):  # pylint: disable=unused-argument
        if args[:2] == ["git", "fetch"]:
            return MagicMock(returncode=0, stdout="", stderr="")
        if args[:2] == ["git", "log"]:
            raise ValueError("Command failed: bad revision 'FETCH_HEAD'")
        raise AssertionError("unexpected")

    with patch(
        "services.git.get_branch_head_author.run_subprocess", side_effect=fake_run
    ):
        result = get_branch_head_author(
            "/tmp/repo", "https://x-access-token:tok@github.com/o/r.git", "main"
        )

    assert result == "unknown"


def test_strips_trailing_whitespace_from_author():
    def fake_run(args, cwd):  # pylint: disable=unused-argument
        if args[:2] == ["git", "log"]:
            return MagicMock(
                returncode=0, stdout="  Bob <bob@example.com>   \n\n", stderr=""
            )
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch(
        "services.git.get_branch_head_author.run_subprocess", side_effect=fake_run
    ):
        result = get_branch_head_author(
            "/tmp/repo", "https://x-access-token:tok@github.com/o/r.git", "main"
        )

    assert result == "Bob <bob@example.com>"
