# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch

from services.git.reset_pr_branch_to_new_base import reset_pr_branch_to_new_base
from services.types.base_args import BaseArgs


def _make_base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "clone_dir": "/tmp/test-owner/test-repo/pr-123",
            "clone_url": "https://x-access-token:token@github.com/test-owner/test-repo.git",
            "base_branch": "release/20260408",
            "new_branch": "gitauto/schedule-123",
        },
    )


@patch("services.git.reset_pr_branch_to_new_base.git_commit_and_push")
@patch(
    "services.git.reset_pr_branch_to_new_base.reapply_files",
    return_value=["src/app.py", "src/utils.py"],
)
@patch("services.git.reset_pr_branch_to_new_base.git_reset")
@patch("services.git.reset_pr_branch_to_new_base.git_fetch")
@patch(
    "services.git.reset_pr_branch_to_new_base.change_pr_base_branch",
    return_value=True,
)
@patch(
    "services.git.reset_pr_branch_to_new_base.save_pr_files",
    return_value=({"src/app.py": "code\n", "src/utils.py": "util\n"}, []),
)
@patch(
    "services.git.reset_pr_branch_to_new_base.get_pull_request_files",
    return_value=[
        {"filename": "src/app.py", "status": "modified"},
        {"filename": "src/utils.py", "status": "added"},
    ],
)
def test_reset_pr_branch_commits_per_file(
    mock_get_pr_files,
    mock_save,
    mock_update_pr,
    mock_fetch,
    mock_reset,
    mock_reapply,
    mock_commit_push,
):
    result = reset_pr_branch_to_new_base(
        base_args=_make_base_args(), new_base_branch="release/20260422"
    )
    assert result == "Reset 2 files onto release/20260422."
    assert mock_commit_push.call_count == 2
    # First commit gets force=True, second gets force=False
    assert mock_commit_push.call_args_list[0].kwargs["force"] is True
    assert mock_commit_push.call_args_list[1].kwargs["force"] is False
    # Each commit has exactly one file
    assert mock_commit_push.call_args_list[0].kwargs["files"] == ["src/app.py"]
    assert mock_commit_push.call_args_list[1].kwargs["files"] == ["src/utils.py"]


@patch("services.git.reset_pr_branch_to_new_base.git_commit_and_push")
@patch("services.git.reset_pr_branch_to_new_base.reapply_files", return_value=[])
@patch("services.git.reset_pr_branch_to_new_base.git_reset")
@patch("services.git.reset_pr_branch_to_new_base.git_fetch")
@patch(
    "services.git.reset_pr_branch_to_new_base.change_pr_base_branch",
    return_value=True,
)
@patch("services.git.reset_pr_branch_to_new_base.save_pr_files", return_value=({}, []))
@patch(
    "services.git.reset_pr_branch_to_new_base.get_pull_request_files", return_value=[]
)
def test_reset_pr_branch_no_files_skips_commit(
    mock_get_pr_files,
    mock_save,
    mock_update_pr,
    mock_fetch,
    mock_reset,
    mock_reapply,
    mock_commit_push,
):
    result = reset_pr_branch_to_new_base(
        base_args=_make_base_args(), new_base_branch="main"
    )
    assert result == "Changed base to main, no files to rewrite"
    mock_commit_push.assert_not_called()


@patch(
    "services.git.reset_pr_branch_to_new_base.change_pr_base_branch", return_value=False
)
@patch("services.git.reset_pr_branch_to_new_base.save_pr_files", return_value=({}, []))
@patch(
    "services.git.reset_pr_branch_to_new_base.get_pull_request_files", return_value=[]
)
def test_reset_pr_branch_returns_none_on_api_failure(
    mock_get_pr_files,
    mock_save,
    mock_update_pr,
):
    result = reset_pr_branch_to_new_base(
        base_args=_make_base_args(), new_base_branch="main"
    )
    assert result is None
