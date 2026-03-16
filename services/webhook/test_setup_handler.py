# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from anthropic.types import MessageParam

from services.chat_with_agent import AgentResult
from services.github.users.get_user_public_email import UserPublicInfo
from services.webhook.setup_handler import setup_handler

SENDER_INFO = UserPublicInfo(email="test@example.com", display_name="Test User")


def _make_agent_result(is_completed=False):
    messages = cast(list[MessageParam], [{"role": "user", "content": "test"}])
    return AgentResult(
        messages=messages,
        token_input=100,
        token_output=50,
        is_completed=is_completed,
        completion_reason="",
        p=0,
        is_planned=False,
    )


MODULE = "services.webhook.setup_handler"


INSTALLATION = {"owner_id": 1, "installation_id": 123, "owner_type": "Organization"}


@pytest.mark.asyncio
@patch(f"{MODULE}.slack_notify")
@patch(f"{MODULE}.get_pull_request_files", return_value=[])
@patch(f"{MODULE}.update_usage")
@patch(f"{MODULE}.insert_usage", return_value=1)
@patch(f"{MODULE}.delete_remote_branch")
@patch(f"{MODULE}.close_pull_request")
@patch(f"{MODULE}.create_pull_request", return_value=("https://pr", 1))
@patch(f"{MODULE}.create_empty_commit")
@patch(f"{MODULE}.create_remote_branch")
@patch(f"{MODULE}.get_latest_remote_commit_sha", return_value="abc123")
@patch(f"{MODULE}.is_repo_forked", return_value=False)
@patch(f"{MODULE}.get_clone_url", return_value="https://github.com/o/r.git")
@patch(f"{MODULE}.git_clone_to_efs")
@patch(f"{MODULE}.get_efs_dir")
@patch(f"{MODULE}.get_default_branch", return_value="main")
@patch(f"{MODULE}.get_repository_by_name", return_value=None)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
@patch(f"{MODULE}.get_email_from_commits", return_value=None)
@patch(f"{MODULE}.get_user_public_info", return_value=SENDER_INFO)
@patch(f"{MODULE}.chat_with_agent")
async def test_not_completed_closes_pr_and_deletes_branch(
    mock_agent: MagicMock,
    mock_user_info,
    mock_email_from_commits,
    mock_installation,
    mock_repo,
    mock_default_branch,
    mock_efs_dir,
    mock_clone_to_efs,
    mock_clone_url,
    mock_is_fork,
    mock_sha,
    mock_create_branch,
    mock_empty_commit,
    mock_create_pr,
    mock_close_pr,
    mock_delete_branch,
    mock_insert_usage,
    mock_update_usage,
    mock_get_pr_files,
    mock_slack,
    tmp_path,
):
    mock_efs_dir.return_value = str(tmp_path)
    mock_agent.return_value = _make_agent_result(is_completed=False)

    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    mock_clone_to_efs.assert_called_once()
    mock_create_pr.assert_called_once()
    mock_close_pr.assert_called_once()
    mock_delete_branch.assert_called_once()


@pytest.mark.asyncio
@patch(f"{MODULE}.slack_notify")
@patch(f"{MODULE}.get_pull_request_files", return_value=[{"filename": "ci.yml"}])
@patch(f"{MODULE}.update_usage")
@patch(f"{MODULE}.insert_usage", return_value=1)
@patch(f"{MODULE}.delete_remote_branch")
@patch(f"{MODULE}.close_pull_request")
@patch(f"{MODULE}.create_pull_request", return_value=("https://pr", 1))
@patch(f"{MODULE}.create_empty_commit")
@patch(f"{MODULE}.create_remote_branch")
@patch(f"{MODULE}.get_latest_remote_commit_sha", return_value="abc123")
@patch(f"{MODULE}.is_repo_forked", return_value=False)
@patch(f"{MODULE}.get_clone_url", return_value="https://github.com/o/r.git")
@patch(f"{MODULE}.git_clone_to_efs")
@patch(f"{MODULE}.get_efs_dir")
@patch(f"{MODULE}.get_default_branch", return_value="main")
@patch(f"{MODULE}.get_repository_by_name", return_value=None)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
@patch(f"{MODULE}.get_email_from_commits", return_value=None)
@patch(f"{MODULE}.get_user_public_info", return_value=SENDER_INFO)
@patch(f"{MODULE}.chat_with_agent")
async def test_completed_keeps_pr(
    mock_agent: MagicMock,
    mock_user_info,
    mock_email_from_commits,
    mock_installation,
    mock_repo,
    mock_default_branch,
    mock_efs_dir,
    mock_clone_to_efs,
    mock_clone_url,
    mock_is_fork,
    mock_sha,
    mock_create_branch,
    mock_empty_commit,
    mock_create_pr,
    mock_close_pr,
    mock_delete_branch,
    mock_insert_usage,
    mock_update_usage,
    mock_get_pr_files,
    mock_slack,
    tmp_path,
):
    mock_efs_dir.return_value = str(tmp_path)
    mock_agent.return_value = _make_agent_result(is_completed=True)

    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    mock_create_pr.assert_called_once()
    mock_close_pr.assert_not_called()
    mock_delete_branch.assert_not_called()


@pytest.mark.asyncio
@patch(f"{MODULE}.slack_notify")
@patch(f"{MODULE}.get_pull_request_files", return_value=[{"filename": "ci.yml"}])
@patch(f"{MODULE}.update_usage")
@patch(f"{MODULE}.insert_usage", return_value=1)
@patch(f"{MODULE}.delete_remote_branch")
@patch(f"{MODULE}.close_pull_request")
@patch(f"{MODULE}.create_pull_request", return_value=("https://pr", 1))
@patch(f"{MODULE}.create_empty_commit")
@patch(f"{MODULE}.create_remote_branch")
@patch(f"{MODULE}.get_latest_remote_commit_sha", return_value="abc123")
@patch(f"{MODULE}.is_repo_forked", return_value=False)
@patch(f"{MODULE}.get_clone_url", return_value="https://github.com/o/r.git")
@patch(f"{MODULE}.git_clone_to_efs")
@patch(f"{MODULE}.get_efs_dir")
@patch(f"{MODULE}.get_default_branch", return_value="main")
@patch(
    f"{MODULE}.get_repository_by_name",
    return_value={"target_branch": "develop", "repo_id": 456},
)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
@patch(f"{MODULE}.get_email_from_commits", return_value=None)
@patch(f"{MODULE}.get_user_public_info", return_value=SENDER_INFO)
@patch(f"{MODULE}.chat_with_agent")
async def test_uses_target_branch_when_set(
    mock_agent: MagicMock,
    mock_user_info,
    mock_email_from_commits,
    mock_installation,
    mock_repo,
    mock_default_branch,
    mock_efs_dir,
    mock_clone_to_efs,
    mock_clone_url,
    mock_is_fork,
    mock_sha,
    mock_create_branch,
    mock_empty_commit,
    mock_create_pr,
    mock_close_pr,
    mock_delete_branch,
    mock_insert_usage,
    mock_update_usage,
    mock_get_pr_files,
    mock_slack,
    tmp_path,
):
    mock_efs_dir.return_value = str(tmp_path)
    mock_agent.return_value = _make_agent_result(is_completed=True)

    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    # Should use target_branch, not call get_default_branch
    mock_default_branch.assert_not_called()
    # Verify "develop" was passed to Claude
    call_kwargs = mock_agent.call_args.kwargs
    content_blocks = call_kwargs["messages"][0]["content"]
    branch_block = content_blocks[1]["text"]
    assert "develop" in branch_block


@pytest.mark.asyncio
@patch(f"{MODULE}.slack_notify")
@patch(f"{MODULE}.get_pull_request_files", return_value=[{"filename": "ci.yml"}])
@patch(f"{MODULE}.update_usage")
@patch(f"{MODULE}.insert_usage", return_value=1)
@patch(f"{MODULE}.delete_remote_branch")
@patch(f"{MODULE}.close_pull_request")
@patch(f"{MODULE}.create_pull_request", return_value=("https://pr", 1))
@patch(f"{MODULE}.create_empty_commit")
@patch(f"{MODULE}.create_remote_branch")
@patch(f"{MODULE}.get_latest_remote_commit_sha", return_value="abc123")
@patch(f"{MODULE}.is_repo_forked", return_value=False)
@patch(f"{MODULE}.get_clone_url", return_value="https://github.com/o/r.git")
@patch(f"{MODULE}.git_clone_to_efs")
@patch(f"{MODULE}.get_efs_dir")
@patch(f"{MODULE}.get_default_branch", return_value="main")
@patch(f"{MODULE}.get_repository_by_name", return_value=None)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
@patch(f"{MODULE}.get_email_from_commits", return_value=None)
@patch(f"{MODULE}.get_user_public_info", return_value=SENDER_INFO)
@patch(f"{MODULE}.chat_with_agent")
async def test_passes_existing_workflows_to_claude(
    mock_agent: MagicMock,
    mock_user_info,
    mock_email_from_commits,
    mock_installation,
    mock_repo,
    mock_default_branch,
    mock_efs_dir,
    mock_clone_to_efs,
    mock_clone_url,
    mock_is_fork,
    mock_sha,
    mock_create_branch,
    mock_empty_commit,
    mock_create_pr,
    mock_close_pr,
    mock_delete_branch,
    mock_insert_usage,
    mock_update_usage,
    mock_get_pr_files,
    mock_slack,
    tmp_path,
):
    mock_efs_dir.return_value = str(tmp_path)

    # Create local workflow files
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text("name: CI\non: push\n")
    (workflow_dir / "deploy.yml").write_text("name: Deploy\non: push\n")

    mock_agent.return_value = _make_agent_result(is_completed=True)

    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    call_kwargs = mock_agent.call_args.kwargs
    content_blocks = call_kwargs["messages"][0]["content"]
    workflows_block = content_blocks[2]["text"]
    assert "ci.yml" in workflows_block
    assert "deploy.yml" in workflows_block


@pytest.mark.asyncio
@patch(f"{MODULE}.slack_notify")
@patch(f"{MODULE}.get_pull_request_files", return_value=[{"filename": "ci.yml"}])
@patch(f"{MODULE}.update_usage")
@patch(f"{MODULE}.insert_usage", return_value=1)
@patch(f"{MODULE}.delete_remote_branch")
@patch(f"{MODULE}.close_pull_request")
@patch(f"{MODULE}.create_pull_request", return_value=("https://pr", 1))
@patch(f"{MODULE}.create_empty_commit")
@patch(f"{MODULE}.create_remote_branch")
@patch(f"{MODULE}.get_latest_remote_commit_sha", return_value="abc123")
@patch(f"{MODULE}.is_repo_forked", return_value=False)
@patch(f"{MODULE}.get_clone_url", return_value="https://github.com/o/r.git")
@patch(f"{MODULE}.git_clone_to_efs")
@patch(f"{MODULE}.get_efs_dir")
@patch(f"{MODULE}.get_default_branch", return_value="main")
@patch(f"{MODULE}.get_repository_by_name", return_value=None)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
@patch(f"{MODULE}.get_email_from_commits", return_value=None)
@patch(f"{MODULE}.get_user_public_info", return_value=SENDER_INFO)
@patch(f"{MODULE}.chat_with_agent")
async def test_clones_repo_when_efs_dir_missing(
    mock_agent: MagicMock,
    mock_user_info,
    mock_email_from_commits,
    mock_installation,
    mock_repo,
    mock_default_branch,
    mock_efs_dir,
    mock_clone_to_efs,
    mock_clone_url,
    mock_is_fork,
    mock_sha,
    mock_create_branch,
    mock_empty_commit,
    mock_create_pr,
    mock_close_pr,
    mock_delete_branch,
    mock_insert_usage,
    mock_update_usage,
    mock_get_pr_files,
    mock_slack,
    tmp_path,
):
    # Point to a non-existent directory to simulate missing EFS clone
    missing_dir = str(tmp_path / "nonexistent")
    mock_efs_dir.return_value = missing_dir
    # Real git_clone_to_efs creates the directory; simulate that
    mock_clone_to_efs.side_effect = lambda **kwargs: os.makedirs(
        kwargs["efs_dir"], exist_ok=True
    )
    mock_agent.return_value = _make_agent_result(is_completed=True)

    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    # git_clone_to_efs should be called to clone the repo
    mock_clone_to_efs.assert_called_once_with(
        efs_dir=missing_dir,
        clone_url="https://github.com/o/r.git",
        branch="main",
    )
    mock_create_pr.assert_called_once()


@pytest.mark.asyncio
@patch(f"{MODULE}.get_installation_by_owner", return_value=None)
async def test_no_installation_skips(mock_installation):
    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    mock_installation.assert_called_once()


@pytest.mark.asyncio
@patch(f"{MODULE}.get_default_branch", return_value=None)
@patch(f"{MODULE}.get_repository_by_name", return_value=None)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
async def test_empty_repo_skips(mock_installation, mock_repo, mock_default_branch):
    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    mock_default_branch.assert_called_once()


@pytest.mark.asyncio
@patch(f"{MODULE}.slack_notify")
@patch(f"{MODULE}.get_pull_request_files", return_value=[{"filename": "ci.yml"}])
@patch(f"{MODULE}.update_usage")
@patch(f"{MODULE}.insert_usage", return_value=1)
@patch(f"{MODULE}.delete_remote_branch")
@patch(f"{MODULE}.close_pull_request")
@patch(f"{MODULE}.create_pull_request", return_value=("https://pr", 1))
@patch(f"{MODULE}.create_empty_commit")
@patch(f"{MODULE}.create_remote_branch")
@patch(f"{MODULE}.get_latest_remote_commit_sha", return_value="abc123")
@patch(f"{MODULE}.is_repo_forked", return_value=False)
@patch(f"{MODULE}.get_clone_url", return_value="https://github.com/o/r.git")
@patch(f"{MODULE}.git_clone_to_efs")
@patch(f"{MODULE}.get_efs_dir")
@patch(f"{MODULE}.get_default_branch", return_value="main")
@patch(f"{MODULE}.get_repository_by_name", return_value=None)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
@patch(f"{MODULE}.get_email_from_commits", return_value=None)
@patch(f"{MODULE}.get_user_public_info", return_value=SENDER_INFO)
@patch(f"{MODULE}.chat_with_agent")
async def test_system_message_mentions_coverage(
    mock_agent: MagicMock,
    mock_user_info,
    mock_email_from_commits,
    mock_installation,
    mock_repo,
    mock_default_branch,
    mock_efs_dir,
    mock_clone_to_efs,
    mock_clone_url,
    mock_is_fork,
    mock_sha,
    mock_create_branch,
    mock_empty_commit,
    mock_create_pr,
    mock_close_pr,
    mock_delete_branch,
    mock_insert_usage,
    mock_update_usage,
    mock_get_pr_files,
    mock_slack,
    tmp_path,
):
    mock_efs_dir.return_value = str(tmp_path)
    mock_agent.return_value = _make_agent_result(is_completed=True)

    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    call_kwargs = mock_agent.call_args.kwargs
    assert "coverage" in call_kwargs["system_message"].lower()
    assert "coverage-report" in call_kwargs["system_message"]


@pytest.mark.asyncio
@patch(f"{MODULE}.slack_notify")
@patch(f"{MODULE}.get_pull_request_files", return_value=[{"filename": "ci.yml"}])
@patch(f"{MODULE}.update_usage")
@patch(f"{MODULE}.insert_usage", return_value=1)
@patch(f"{MODULE}.delete_remote_branch")
@patch(f"{MODULE}.close_pull_request")
@patch(f"{MODULE}.create_pull_request", return_value=("https://pr", 1))
@patch(f"{MODULE}.create_empty_commit")
@patch(f"{MODULE}.create_remote_branch")
@patch(f"{MODULE}.get_latest_remote_commit_sha", return_value="abc123")
@patch(f"{MODULE}.is_repo_forked", return_value=False)
@patch(f"{MODULE}.get_clone_url", return_value="https://github.com/o/r.git")
@patch(f"{MODULE}.git_clone_to_efs")
@patch(f"{MODULE}.get_efs_dir")
@patch(f"{MODULE}.get_default_branch", return_value="main")
@patch(f"{MODULE}.get_repository_by_name", return_value=None)
@patch(f"{MODULE}.get_installation_by_owner", return_value=INSTALLATION)
@patch(f"{MODULE}.get_email_from_commits", return_value=None)
@patch(f"{MODULE}.get_user_public_info", return_value=SENDER_INFO)
@patch(f"{MODULE}.chat_with_agent")
async def test_sets_pr_number_in_base_args(
    mock_agent: MagicMock,
    mock_user_info,
    mock_email_from_commits,
    mock_installation,
    mock_repo,
    mock_default_branch,
    mock_efs_dir,
    mock_clone_to_efs,
    mock_clone_url,
    mock_is_fork,
    mock_sha,
    mock_create_branch,
    mock_empty_commit,
    mock_create_pr,
    mock_close_pr,
    mock_delete_branch,
    mock_insert_usage,
    mock_update_usage,
    mock_get_pr_files,
    mock_slack,
    tmp_path,
):
    mock_efs_dir.return_value = str(tmp_path)
    mock_agent.return_value = _make_agent_result(is_completed=True)

    await setup_handler(
        owner_name="test-owner",
        repo_name="test-repo",
        token="test-token",
        sender_id=123,
        sender_name="test-user",
    )

    call_kwargs = mock_agent.call_args.kwargs
    assert call_kwargs["base_args"]["pr_number"] == 1
