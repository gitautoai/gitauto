# pyright: reportUnusedVariable=false
from unittest.mock import patch, Mock

from services.git.git_diff import git_diff


@patch("services.git.git_diff.run_subprocess")
def test_returns_diff_for_specific_file(mock_run, create_test_base_args):
    mock_run.return_value = Mock(stdout="diff --git a/file.py b/file.py\n-old\n+new\n")
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args, file_path="file.py")

    assert "diff --git" in result
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

    assert "No diff found" in result


@patch("services.git.git_diff.run_subprocess")
def test_truncates_large_diff(mock_run, create_test_base_args):
    large_diff = "x" * 60_000
    mock_run.return_value = Mock(stdout=large_diff)
    base_args = create_test_base_args(clone_dir="/tmp/repo", base_branch="main")

    result = git_diff(base_args=base_args)

    assert len(result) < 60_000
    assert "truncated" in result
    assert "60,000" in result


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
