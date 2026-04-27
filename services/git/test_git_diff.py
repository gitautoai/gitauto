# pyright: reportUnusedVariable=false
# pylint: disable=unused-argument
from unittest.mock import patch, Mock

from services.git.git_diff import git_diff


@patch("services.git.git_diff.run_subprocess")
def test_returns_diff_for_specific_file(mock_run, create_test_base_args):
    mock_run.return_value = Mock(stdout="diff --git a/file.py b/file.py\n-old\n+new\n")
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args, file_path="file.py")

    assert result == "diff --git a/file.py b/file.py\n-old\n+new\n"
    mock_run.assert_called_once_with(
        args=["git", "diff", "origin/main...HEAD", "--", "file.py"],
        cwd="/tmp/repo",
    )


@patch("services.git.git_diff.run_subprocess")
def test_returns_diff_for_all_files_when_no_path(mock_run, create_test_base_args):
    mock_run.return_value = Mock(stdout="diff output")
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args)

    assert result == "diff output"
    mock_run.assert_called_once_with(
        args=["git", "diff", "origin/main...HEAD"],
        cwd="/tmp/repo",
    )


@patch("services.git.git_diff.run_subprocess")
def test_returns_message_when_no_diff(mock_run, create_test_base_args):
    mock_run.return_value = Mock(stdout="")
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args, file_path="unchanged.py")

    assert result == "No diff found for unchanged.py between origin/main and HEAD."


@patch("services.git.git_diff.run_subprocess")
def test_truncates_large_diff(mock_run, create_test_base_args):
    large_diff = "x" * 60_000
    mock_run.return_value = Mock(stdout=large_diff)
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args)

    # max_chars = 50_000 in git_diff.py; the marker carries len(diff) formatted with thousands separators.
    assert result == ("x" * 50_000) + "\n... [truncated, 60,000 chars total]"


@patch("services.git.git_diff.run_subprocess")
def test_strips_leading_slash_from_file_path(mock_run, create_test_base_args):
    mock_run.return_value = Mock(stdout="diff")
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    git_diff(base_args=base_args, file_path="/src/file.py")

    mock_run.assert_called_once_with(
        args=["git", "diff", "origin/main...HEAD", "--", "src/file.py"],
        cwd="/tmp/repo",
    )


@patch("services.git.git_diff.run_subprocess", side_effect=ValueError("Command failed"))
def test_returns_default_on_error(_mock_run, create_test_base_args):
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args)

    assert result == "Failed to get git diff."


@patch("services.git.git_diff.deepen_until_merge_base")
@patch("services.git.git_diff.run_subprocess")
def test_delegates_to_deepen_helper_on_no_merge_base(
    mock_run, mock_deepen, create_test_base_args
):
    """Sentry AGENT-3JQ/3J2/3J3 (gitautoai/website PR 821, 2026-04-20): git_diff fired against a shallow clone (git clone --depth 1 + git fetch --depth 1) and the three-dot syntax origin/main...HEAD failed with 'no merge base'. Fix: catch that specific error, hand off to deepen_until_merge_base (the shared helper used by git_merge_base_into_pr too), retry the diff. The exponential schedule itself is tested in services/git/test_deepen_until_merge_base.py — here we only assert the delegation."""
    diff_calls = {"count": 0}

    def mock_subprocess(args, cwd):
        if args[:2] == ["git", "diff"]:
            diff_calls["count"] += 1
            if diff_calls["count"] == 1:
                raise ValueError(
                    "Command failed: fatal: origin/main...HEAD: no merge base"
                )
            return Mock(stdout="diff --git a/file.py b/file.py\n+added\n")
        return Mock(stdout="")

    mock_run.side_effect = mock_subprocess
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args, file_path="file.py")

    assert result == "diff --git a/file.py b/file.py\n+added\n"
    mock_deepen.assert_called_once_with("/tmp/repo", "main")
    # diff was called twice: once before deepen (raised), once after.
    assert diff_calls["count"] == 2


@patch(
    "services.git.git_diff.run_subprocess",
    side_effect=ValueError("Command failed: fatal: unrelated git error"),
)
def test_non_merge_base_error_still_propagates_to_handler(
    _mock_run, create_test_base_args
):
    """Any error other than 'no merge base' must not trigger deepen — deepen is
    a known-safe retry for shallow clones only. Other failures fall through to
    @handle_exceptions which returns the default error string."""
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args)

    assert result == "Failed to get git diff."
