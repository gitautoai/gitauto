from datetime import datetime
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import PRODUCT_ID
from services.webhook.issue_handler import create_pr_from_issue


@pytest.fixture
def mock_base_args():
    return {
        "installation_id": 123456,
        "owner_id": 789012,
        "owner": "test-owner",
        "owner_type": "Organization",
        "repo_id": 345678,
        "repo": "test-repo",
        "issue_number": 42,
        "issue_title": "Test Issue",
        "issue_body": "Test issue body",
        "issuer_name": "test-issuer",
        "parent_issue_number": None,
        "parent_issue_title": None,
        "parent_issue_body": None,
        "new_branch": "test-branch",
        "sender_id": 901234,
        "sender_name": "test-sender",
        "sender_email": "test@example.com",
        "github_urls": [],
        "token": "test-token",
        "is_automation": False,
        "comment_url": None,
    }


@pytest.fixture
def mock_payload():
    return {
        "label": {"name": PRODUCT_ID},
        "issue": {
            "number": 42,
            "title": "Test Issue",
            "body": "Test issue body",
        },
        "repository": {
            "name": "test-repo",
            "id": 345678,
            "owner": {
                "login": "test-owner",
                "type": "Organization",
                "id": 789012,
            },
        },
        "installation": {"id": 123456},
        "sender": {
            "id": 901234,
            "login": "test-sender",
        },
    }


@pytest.mark.asyncio
async def test_create_pr_from_issue_label_mismatch():
    """Test early return when label doesn't match PRODUCT_ID"""
    payload = {"label": {"name": "wrong-label"}}
    result = await create_pr_from_issue(
        payload=payload,
        trigger_type="label",
        input_from="github"
    )
    assert result is None


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_github_input(mock_deconstruct, mock_base_args):
    """Test handling GitHub input source"""
    mock_deconstruct.return_value = (mock_base_args, {})
    
    with patch("services.webhook.issue_handler.delete_comments_by_identifiers") as mock_delete:
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label",
            input_from="github"
        )
        mock_delete.assert_called_once()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.deconstruct_jira_payload")
async def test_create_pr_from_issue_jira_input(mock_deconstruct, mock_base_args):
    """Test handling Jira input source"""
    mock_deconstruct.return_value = (mock_base_args, {})
    
    with patch("services.webhook.issue_handler.delete_comments_by_identifiers") as mock_delete:
        await create_pr_from_issue(
            payload={},
            trigger_type="label",
            input_from="jira"
        )
        mock_delete.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_progress_tracking(mock_deconstruct, mock_create_comment, mock_base_args):
    """Test progress bar creation and updates"""
    mock_deconstruct.return_value = (mock_base_args, {})
    mock_create_comment.return_value = "test-comment-url"

    with patch("services.webhook.issue_handler.update_comment") as mock_update:
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label",
            input_from="github"
        )
        
        assert mock_create_comment.called
        assert mock_update.called
        # First progress update should be at 0%
        first_call = mock_create_comment.call_args[1]
        assert "0%" in first_call["body"]


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.is_request_limit_reached")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_request_limit(mock_deconstruct, mock_limit_check, mock_base_args):
    """Test handling when request limit is reached"""
    mock_deconstruct.return_value = (mock_base_args, {})
    mock_limit_check.return_value = (True, 0, 10, "2025-12-31")

    with patch("services.webhook.issue_handler.update_comment") as mock_update:
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label", 
            input_from="github"
        )
        
        mock_update.assert_called_once()
        update_call = mock_update.call_args[1]
        assert "request limit" in update_call["body"].lower()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.deconstruct_github_payload") 
async def test_create_pr_from_issue_usage_tracking(mock_deconstruct, mock_create_request, mock_base_args):
    """Test usage tracking creation"""
    mock_deconstruct.return_value = (mock_base_args, {})
    mock_create_request.return_value = "test-usage-id"

    with patch("services.webhook.issue_handler.is_request_limit_reached") as mock_limit:
        mock_limit.return_value = (False, 5, 10, None)
        
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label",
            input_from="github"
        )

        mock_create_request.assert_called_once_with(
            user_id=mock_base_args["sender_id"],
            user_name=mock_base_args["sender_name"],
            installation_id=mock_base_args["installation_id"],
            owner_id=mock_base_args["owner_id"],
            owner_type=mock_base_args["owner_type"],
            owner_name=mock_base_args["owner"],
            repo_id=mock_base_args["repo_id"],
            repo_name=mock_base_args["repo"],
            issue_number=mock_base_args["issue_number"],
            source="github",
            email=mock_base_args["sender_email"],
        )


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.get_file_tree")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_file_tree(mock_deconstruct, mock_get_tree, mock_base_args):
    """Test file tree retrieval and processing"""
    mock_deconstruct.return_value = (mock_base_args, {})
    mock_get_tree.return_value = (["file1.py", "file2.py"], "Found 2 files")

    with patch("services.webhook.issue_handler.is_request_limit_reached") as mock_limit:
        mock_limit.return_value = (False, 5, 10, None)
        
        with patch("services.webhook.issue_handler.find_config_files") as mock_find_config:
            mock_find_config.return_value = ["config.yml"]
            
            await create_pr_from_issue(
                payload={"label": {"name": PRODUCT_ID}},
                trigger_type="label",
                input_from="github"
            )

            mock_get_tree.assert_called_once()
            mock_find_config.assert_called_once_with(file_tree=["file1.py", "file2.py"])


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_chat_agent(mock_deconstruct, mock_chat, mock_base_args):
    """Test interaction with chat agent"""
    mock_deconstruct.return_value = (mock_base_args, {})
    mock_chat.return_value = (
        [], [], "test-tool", {}, 100, 200, True, 50
    )

    with patch.multiple(
        "services.webhook.issue_handler",
        is_request_limit_reached=MagicMock(return_value=(False, 5, 10, None)),
        get_file_tree=MagicMock(return_value=([], "")),
        create_system_messages=MagicMock(return_value=[]),
    ):
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label",
            input_from="github"
        )

        assert mock_chat.call_count >= 1
        first_call = mock_chat.call_args_list[0][1]
        assert "messages" in first_call
        assert "system_messages" in first_call
        assert first_call["mode"] in ["explore", "commit"]


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_pr_creation(mock_deconstruct, mock_create_pr, mock_base_args):
    """Test pull request creation"""
    mock_deconstruct.return_value = (mock_base_args, {})
    mock_create_pr.return_value = "https://github.com/test-owner/test-repo/pull/1"

    with patch.multiple(
        "services.webhook.issue_handler",
        is_request_limit_reached=MagicMock(return_value=(False, 5, 10, None)),
        get_file_tree=MagicMock(return_value=([], "")),
        create_system_messages=MagicMock(return_value=[]),
        chat_with_agent=MagicMock(return_value=([], [], None, None, 0, 0, False, 90)),
    ):
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label",
            input_from="github"
        )

        mock_create_pr.assert_called_once()
        call_args = mock_create_pr.call_args[1]
        assert "Resolves #" in call_args["body"]


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_usage_update(mock_deconstruct, mock_update_usage, mock_base_args):
    """Test usage statistics update"""
    mock_deconstruct.return_value = (mock_base_args, {})
    usage_id = "test-usage-id"

    with patch.multiple(
        "services.webhook.issue_handler",
        is_request_limit_reached=MagicMock(return_value=(False, 5, 10, None)),
        create_user_request=MagicMock(return_value=usage_id),
        get_file_tree=MagicMock(return_value=([], "")),
        create_system_messages=MagicMock(return_value=[]),
        chat_with_agent=MagicMock(return_value=([], [], None, None, 100, 200, False, 90)),
        create_pull_request=MagicMock(return_value="https://github.com/test-owner/test-repo/pull/1"),
    ):
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label",
            input_from="github"
        )

        mock_update_usage.assert_called_once()
        call_args = mock_update_usage.call_args[1]
        assert call_args["usage_record_id"] == usage_id
        assert call_args["is_completed"] is True
        assert call_args["token_input"] == 100
        assert call_args["token_output"] == 200
        assert isinstance(call_args["total_seconds"], int)


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.check_branch_exists")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_create_pr_from_issue_deleted_branch(mock_deconstruct, mock_check_branch, mock_base_args):
    """Test handling of deleted branch during execution"""
    mock_deconstruct.return_value = (mock_base_args, {})
    mock_check_branch.return_value = False

    with patch.multiple(
        "services.webhook.issue_handler",
        is_request_limit_reached=MagicMock(return_value=(False, 5, 10, None)),
        get_file_tree=MagicMock(return_value=([], "")),
        create_system_messages=MagicMock(return_value=[]),
        update_comment=MagicMock(),
    ):
        await create_pr_from_issue(
            payload={"label": {"name": PRODUCT_ID}},
            trigger_type="label",
            input_from="github"
        )

        mock_check_branch.assert_called_once_with(
            owner=mock_base_args["owner"],
            repo=mock_base_args["repo"],
            branch_name=mock_base_args["new_branch"],
            token=mock_base_args["token"]
        )