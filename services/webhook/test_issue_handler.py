import asyncio
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock, call

import pytest

from config import PRODUCT_ID, PR_BODY_STARTS_WITH
from constants.messages import COMPLETED_PR, SETTINGS_LINKS
from services.supabase.usage.insert_usage import Trigger
from services.webhook.issue_handler import create_pr_from_issue
from utils.text.comment_identifiers import PROGRESS_BAR_FILLED, PROGRESS_BAR_EMPTY
from utils.text.text_copy import UPDATE_COMMENT_FOR_422


@pytest.fixture
def github_payload():
    """Fixture to provide a sample GitHub payload."""
    return {
        "label": {"name": PRODUCT_ID},
        "repository": {"name": "test-repo", "owner": {"login": "test-owner"}},
        "issue": {"number": 123, "title": "Test Issue", "body": "Test body"},
        "sender": {"login": "test-sender"},
    }


@pytest.fixture
def jira_payload():
    """Fixture to provide a sample Jira payload."""
    return {
        "issue": {
            "key": "JIRA-123",
            "fields": {
                "summary": "Test Jira Issue",
                "description": "Test Jira description",
            }
        },
        "user": {"displayName": "jira-user"},
    }


@pytest.fixture
def mock_base_args():
    """Fixture to provide mock base arguments."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "issue_number": 123,
        "issue_title": "Test Issue",
        "issue_body": "Test body" + SETTINGS_LINKS,
        "sender_name": "test-sender",
        "installation_id": 456,
        "owner_id": 789,
        "owner_type": "Organization",
        "repo_id": 101112,
        "issuer_name": "test-issuer",
        "parent_issue_number": None,
        "parent_issue_title": None,
        "parent_issue_body": None,
        "new_branch": "test-branch",
        "sender_id": 131415,
        "sender_email": "test@example.com",
        "github_urls": ["https://github.com/test-owner/test-repo/blob/main/README.md"],
        "other_urls": [],
        "token": "test-token",
        "is_automation": False,
        "clone_url": "https://github.com/test-owner/test-repo.git",
        "comment_url": "https://api.github.com/repos/test-owner/test-repo/issues/comments/123456",
        "issue_comments": []
    }


@pytest.fixture
def mock_repo_settings():
    """Fixture to provide mock repository settings."""
    return {"setting1": "value1", "setting2": "value2"}


@pytest.fixture
def mock_time():
    """Fixture to mock time.time()."""
    with patch("services.webhook.issue_handler.time.time") as mock:
        mock.return_value = 1000.0
        yield mock


@pytest.fixture
def mock_datetime():
    """Fixture to mock datetime.now()."""
    with patch("services.webhook.issue_handler.datetime") as mock:
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2025-07-05"
        mock.now.return_value = mock_now
        yield mock


@pytest.fixture
def mock_slack_notify():
    """Fixture to mock slack_notify."""
    with patch("services.webhook.issue_handler.slack_notify") as mock:
        mock.return_value = "thread-ts-123"
        yield mock


@pytest.fixture
def mock_deconstruct_github_payload():
    """Fixture to mock deconstruct_github_payload."""
    with patch("services.webhook.issue_handler.deconstruct_github_payload") as mock:
        yield mock


@pytest.fixture
def mock_deconstruct_jira_payload():
    """Fixture to mock deconstruct_jira_payload."""
    with patch("services.webhook.issue_handler.deconstruct_jira_payload") as mock:
        yield mock


@pytest.fixture
def mock_delete_comments_by_identifiers():
    """Fixture to mock delete_comments_by_identifiers."""
    with patch("services.webhook.issue_handler.delete_comments_by_identifiers") as mock:
        yield mock


@pytest.fixture
def mock_create_progress_bar():
    """Fixture to mock create_progress_bar."""
    with patch("services.webhook.issue_handler.create_progress_bar") as mock:
        mock.return_value = "Progress: [=====>     ] 50%"
        yield mock


@pytest.fixture
def mock_create_comment():
    """Fixture to mock create_comment."""
    with patch("services.webhook.issue_handler.create_comment") as mock:
        mock.return_value = "https://api.github.com/repos/test-owner/test-repo/issues/comments/123456"
        yield mock


@pytest.fixture
def mock_update_comment():
    """Fixture to mock update_comment."""
    with patch("services.webhook.issue_handler.update_comment") as mock:
        yield mock


@pytest.fixture
def mock_render_text():
    """Fixture to mock render_text."""
    with patch("services.webhook.issue_handler.render_text") as mock:
        mock.return_value = "Rendered text"
        yield mock


@pytest.fixture
def mock_is_request_limit_reached():
    """Fixture to mock is_request_limit_reached."""
    with patch("services.webhook.issue_handler.is_request_limit_reached") as mock:
        mock.return_value = (False, 10, 20, "2025-08-01")
        yield mock


@pytest.fixture
def mock_create_user_request():
    """Fixture to mock create_user_request."""
    with patch("services.webhook.issue_handler.create_user_request") as mock:
        mock.return_value = "usage-record-id-123"
        yield mock


@pytest.fixture
def mock_add_reaction_to_issue():
    """Fixture to mock add_reaction_to_issue."""
    with patch("services.webhook.issue_handler.add_reaction_to_issue") as mock:
        mock.return_value = AsyncMock()
        yield mock


@pytest.fixture
def mock_create_task():
    """Fixture to mock create_task."""
    with patch("services.webhook.issue_handler.create_task") as mock:
        yield mock


@pytest.fixture
def mock_get_file_tree_list():
    """Fixture to mock get_file_tree_list."""
    with patch("services.webhook.issue_handler.get_file_tree_list") as mock:
        mock.return_value = (["file1.py", "file2.py"], "Found 2 files")
        yield mock


@pytest.fixture
def mock_find_config_files():
    """Fixture to mock find_config_files."""
    with patch("services.webhook.issue_handler.find_config_files") as mock:
        mock.return_value = ["config1.json", "config2.yaml"]
        yield mock


@pytest.fixture
def mock_get_remote_file_content():
    """Fixture to mock get_remote_file_content."""
    with patch("services.webhook.issue_handler.get_remote_file_content") as mock:
        mock.return_value = "file content"
        yield mock


@pytest.fixture
def mock_get_comments():
    """Fixture to mock get_comments."""
    with patch("services.webhook.issue_handler.get_comments") as mock:
        mock.return_value = ["Comment 1", "Comment 2"]
        yield mock


@pytest.fixture
def mock_extract_image_urls():
    """Fixture to mock extract_image_urls."""
    with patch("services.webhook.issue_handler.extract_image_urls") as mock:
        mock.return_value = [{"url": "https://example.com/image.png", "alt": "Test Image"}]
        yield mock


@pytest.fixture
def mock_get_base64():
    """Fixture to mock get_base64."""
    with patch("services.webhook.issue_handler.get_base64") as mock:
        mock.return_value = "base64-encoded-image"
        yield mock


@pytest.fixture
def mock_describe_image():
    """Fixture to mock describe_image."""
    with patch("services.webhook.issue_handler.describe_image") as mock:
        mock.return_value = "This is an image description"
        yield mock


@pytest.fixture
def mock_get_remote_file_content_by_url():
    """Fixture to mock get_remote_file_content_by_url."""
    with patch("services.webhook.issue_handler.get_remote_file_content_by_url") as mock:
        mock.return_value = "file content from URL"
        yield mock


@pytest.fixture
def mock_get_latest_remote_commit_sha():
    """Fixture to mock get_latest_remote_commit_sha."""
    with patch("services.webhook.issue_handler.get_latest_remote_commit_sha") as mock:
        mock.return_value = "abc123def456"
        yield mock


@pytest.fixture
def mock_create_remote_branch():
    """Fixture to mock create_remote_branch."""
    with patch("services.webhook.issue_handler.create_remote_branch") as mock:
        yield mock


@pytest.fixture
def mock_is_lambda_timeout_approaching():
    """Fixture to mock is_lambda_timeout_approaching."""
    with patch("services.webhook.issue_handler.is_lambda_timeout_approaching") as mock:
        # First call returns not approaching timeout, second call returns approaching timeout
        mock.side_effect = [(False, 10.0), (True, 890.0)]
        yield mock


@pytest.fixture
def mock_get_timeout_message():
    """Fixture to mock get_timeout_message."""
    with patch("services.webhook.issue_handler.get_timeout_message") as mock:
        mock.return_value = "Approaching timeout after 890.0 seconds"
        yield mock


@pytest.fixture
def mock_check_branch_exists():
    """Fixture to mock check_branch_exists."""
    with patch("services.webhook.issue_handler.check_branch_exists") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_chat_with_agent():
    """Fixture to mock chat_with_agent."""
    with patch("services.webhook.issue_handler.chat_with_agent") as mock:
        # First call (explore) returns is_explored=True
        # Second call (commit) returns is_committed=True
        # Third call (explore) returns is_explored=False
        # Fourth call (commit) returns is_committed=False
        mock.side_effect = [
            (
                [{"role": "user", "content": "test"}],  # messages
                ["previous_call_1"],  # previous_calls
                "explore",  # tool_name
                {"arg1": "value1"},  # tool_args
                100,  # token_input
                200,  # token_output
                True,  # is_explored/is_committed
                15,  # p
            ),
            (
                [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}],
                ["previous_call_1", "previous_call_2"],
                "commit",
                {"arg2": "value2"},
                150,
                250,
                True,
                25,
            ),
            (
                [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}, {"role": "user", "content": "follow-up"}],
                ["previous_call_1", "previous_call_2", "previous_call_3"],
                "explore",
                {"arg3": "value3"},
                200,
                300,
                False,
                35,
            ),
            (
                [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}, {"role": "user", "content": "follow-up"}, {"role": "assistant", "content": "final"}],
                ["previous_call_1", "previous_call_2", "previous_call_3", "previous_call_4"],
                "commit",
                {"arg4": "value4"},
                250,
                350,
                False,
                45,
            ),
        ]
        yield mock


@pytest.fixture
def mock_create_empty_commit():
    """Fixture to mock create_empty_commit."""
    with patch("services.webhook.issue_handler.create_empty_commit") as mock:
        yield mock


@pytest.fixture
def mock_create_pull_request():
    """Fixture to mock create_pull_request."""
    with patch("services.webhook.issue_handler.create_pull_request") as mock:
        mock.return_value = "https://github.com/test-owner/test-repo/pull/456"
        yield mock


@pytest.fixture
def mock_pull_request_completed():
    """Fixture to mock pull_request_completed."""
    with patch("services.webhook.issue_handler.pull_request_completed") as mock:
        mock.return_value = "PR completed successfully"
        yield mock


@pytest.fixture
def mock_update_usage():
    """Fixture to mock update_usage."""
    with patch("services.webhook.issue_handler.update_usage") as mock:
        yield mock


@pytest.fixture
def mock_git_command():
    """Fixture to mock git_command."""
    with patch("services.webhook.issue_handler.git_command") as mock:
        mock.return_value = "git checkout test-branch"
        yield mock


@pytest.mark.asyncio
async def test_create_pr_from_issue_github_happy_path(
    github_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_datetime,
    mock_slack_notify,
    mock_deconstruct_github_payload,
    mock_delete_comments_by_identifiers,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_render_text,
    mock_is_request_limit_reached,
    mock_create_user_request,
    mock_create_task,
    mock_add_reaction_to_issue,
    mock_get_file_tree_list,
    mock_find_config_files,
    mock_get_remote_file_content,
    mock_get_comments,
    mock_extract_image_urls,
    mock_get_base64,
    mock_describe_image,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_lambda_timeout_approaching,
    mock_check_branch_exists,
    mock_chat_with_agent,
    mock_create_empty_commit,
    mock_create_pull_request,
    mock_pull_request_completed,
    mock_update_usage,
    mock_git_command,
):
    """Test the happy path for GitHub input."""
    # Setup
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
    
    # Execute
    await create_pr_from_issue(github_payload, "issue_comment", "github")
    
    # Verify
    # Check that slack_notify was called with the expected sequence of calls
    expected_calls = [
        call("Issue handler started: `issue_comment` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`"),
        call("PR created for test-owner/test-repo", "thread-ts-123"),
        call("Completed", "thread-ts-123")
    ]
    mock_slack_notify.assert_has_calls(expected_calls)
    mock_deconstruct_github_payload.assert_called_once_with(payload=github_payload)
    mock_delete_comments_by_identifiers.assert_called_once()
    mock_create_comment.assert_called()
    mock_is_request_limit_reached.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_create_task.assert_called_once()
    mock_get_file_tree_list.assert_called_once()
    mock_find_config_files.assert_called_once()
    mock_get_comments.assert_called_once()
    mock_extract_image_urls.assert_called()
    mock_get_latest_remote_commit_sha.assert_called_once()
    mock_create_remote_branch.assert_called_once()
    mock_chat_with_agent.assert_called()
    mock_create_empty_commit.assert_called_once()
    mock_create_pull_request.assert_called_once()
    mock_update_usage.assert_called_once_with(
        usage_record_id="usage-record-id-123",
        is_completed=True,
        pr_number=456,
        token_input=0,
        token_output=0,
        total_seconds=0,
    )


@pytest.mark.asyncio
async def test_create_pr_from_issue_jira_happy_path(
    jira_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_datetime,
    mock_slack_notify,
    mock_deconstruct_jira_payload,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_render_text,
    mock_is_request_limit_reached,
    mock_create_user_request,
    mock_get_file_tree_list,
    mock_find_config_files,
    mock_get_remote_file_content,
    mock_extract_image_urls,
    mock_get_base64,
    mock_describe_image,
    mock_get_remote_file_content_by_url,
    mock_create_remote_branch,
    mock_is_lambda_timeout_approaching,
    mock_check_branch_exists,
    mock_chat_with_agent,
    mock_create_empty_commit,
    mock_create_pull_request,
    mock_pull_request_completed,
    mock_update_usage,
    mock_git_command,
):
    """Test the happy path for Jira input."""
    # Setup
    mock_deconstruct_jira_payload.return_value = (mock_base_args, mock_repo_settings)
    
    # Execute
    await create_pr_from_issue(jira_payload, "jira_issue", "jira")
    
    # Verify
    # Check that slack_notify was called with the expected sequence of calls
    expected_calls = [
        call("Issue handler started: `jira_issue` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`"),
        call("Completed", "thread-ts-123")
        call("PR created for test-owner/test-repo", "thread-ts-123"),
    ]
    mock_slack_notify.assert_has_calls(expected_calls)
    mock_deconstruct_jira_payload.assert_called_once_with(payload=jira_payload)
    mock_create_comment.assert_called()
    mock_is_request_limit_reached.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_file_tree_list.assert_called_once()
    mock_find_config_files.assert_called_once()
    mock_extract_image_urls.assert_called()
    mock_create_remote_branch.assert_called_once()
    mock_chat_with_agent.assert_called()
    mock_create_empty_commit.assert_called_once()
    mock_create_pull_request.assert_called_once()
    mock_update_usage.assert_called_once()


@pytest.mark.asyncio
async def test_create_pr_from_issue_label_mismatch(
    github_payload,
    mock_time,
    mock_slack_notify,
    mock_deconstruct_github_payload,
):
    """Test early return when label doesn't match PRODUCT_ID."""
    # Setup
    modified_payload = github_payload.copy()
    modified_payload["label"] = {"name": "not-matching-label"}
    
    # Execute
    await create_pr_from_issue(modified_payload, "issue_label", "github")
    
    # Verify
    mock_deconstruct_github_payload.assert_not_called()
    mock_slack_notify.assert_not_called()


@pytest.mark.asyncio
async def test_create_pr_from_issue_request_limit_reached(
    github_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_slack_notify,
    mock_deconstruct_github_payload,
    mock_delete_comments_by_identifiers,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_is_request_limit_reached,
):
    """Test early return when request limit is reached."""
    # Setup
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
    mock_is_request_limit_reached.return_value = (True, 0, 20, "2025-08-01")
    
    with patch("services.webhook.issue_handler.request_limit_reached") as mock_request_limit_reached:
        mock_request_limit_reached.return_value = "Request limit reached message"
        
        # Execute
        await create_pr_from_issue(github_payload, "issue_comment", "github")
        
        # Verify
        # Check that slack_notify was called with the expected sequence of calls
        expected_calls = [
            call("Issue handler started: `issue_comment` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`"),
            call("Request limit reached for test-owner/test-repo - 20 requests used", "thread-ts-123")
        ]
        mock_slack_notify.assert_has_calls(expected_calls)
        mock_update_comment.assert_called_with(body="Request limit reached message", base_args=mock_base_args)
        mock_request_limit_reached.assert_called_once_with(user_name="test-sender", request_count=20, end_date="2025-08-01")


@pytest.mark.asyncio
async def test_create_pr_from_issue_branch_deleted(
    github_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_datetime,
    mock_slack_notify,
    mock_deconstruct_github_payload,
    mock_delete_comments_by_identifiers,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_render_text,
    mock_is_request_limit_reached,
    mock_create_user_request,
    mock_create_task,
    mock_add_reaction_to_issue,
    mock_get_file_tree_list,
    mock_find_config_files,
    mock_get_remote_file_content,
    mock_get_comments,
    mock_extract_image_urls,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_check_branch_exists,
):
    """Test early break from loop when branch is deleted."""
    # Setup
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
    mock_check_branch_exists.return_value = False
    
    # Execute
    await create_pr_from_issue(github_payload, "issue_comment", "github")
    
    # Verify
    mock_check_branch_exists.assert_called_once_with(
        owner="test-owner", 
        repo="test-repo", 
        branch_name="test-branch", 
        token="test-token"
    )
    mock_update_comment.assert_called_with(
        body="Process stopped: Branch 'test-branch' has been deleted", 
        base_args=mock_base_args
    )
    # Should only call slack_notify once for the start message
    mock_slack_notify.assert_called_once_with("Issue handler started: `issue_comment` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`")


@pytest.mark.asyncio
async def test_create_pr_from_issue_timeout_approaching(
    github_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_datetime,
    mock_slack_notify,
    mock_deconstruct_github_payload,
    mock_delete_comments_by_identifiers,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_render_text,
    mock_is_request_limit_reached,
    mock_create_user_request,
    mock_create_task,
    mock_add_reaction_to_issue,
    mock_get_file_tree_list,
    mock_find_config_files,
    mock_get_remote_file_content,
    mock_get_comments,
    mock_extract_image_urls,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_lambda_timeout_approaching,
    mock_get_timeout_message,
    mock_check_branch_exists,
):
    """Test early break from loop when timeout is approaching."""
    # Setup
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
    mock_is_lambda_timeout_approaching.return_value = (True, 890.0)
    
    # Execute
    await create_pr_from_issue(github_payload, "issue_comment", "github")
    
    # Verify
    mock_is_lambda_timeout_approaching.assert_called_once_with(1000.0)
    mock_get_timeout_message.assert_called_once_with(890.0, "Issue processing")
    # Should call slack_notify for start and completion
    expected_calls = [
        call("Issue handler started: `issue_comment` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`"),
        call("Completed", "thread-ts-123")
    ]
    mock_slack_notify.assert_has_calls(expected_calls)

        call("PR created for test-owner/test-repo", "thread-ts-123"),

@pytest.mark.asyncio
async def test_create_pr_from_issue_pr_creation_failed(
    github_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_datetime,
    mock_slack_notify,
    mock_deconstruct_github_payload,
    mock_delete_comments_by_identifiers,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_render_text,
    mock_is_request_limit_reached,
    mock_create_user_request,
    mock_create_task,
    mock_add_reaction_to_issue,
    mock_get_file_tree_list,
    mock_find_config_files,
    mock_get_remote_file_content,
    mock_get_comments,
    mock_extract_image_urls,
    mock_get_base64,
    mock_describe_image,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_lambda_timeout_approaching,
    mock_check_branch_exists,
    mock_chat_with_agent,
    mock_create_empty_commit,
    mock_create_pull_request,
    mock_update_usage,
    mock_git_command,
):
    """Test scenario when PR creation fails."""
    # Setup
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
    mock_create_pull_request.return_value = None
    
    # Execute
    await create_pr_from_issue(github_payload, "issue_comment", "github")
    
    # Verify
    mock_update_comment.assert_called_with(body=UPDATE_COMMENT_FOR_422, base_args=mock_base_args)
    # Check that slack_notify was called with the expected sequence of calls
    expected_calls = [
        call("Issue handler started: `issue_comment` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`"),
        call("@channel Failed to create PR for test-owner/test-repo", "thread-ts-123"),
        call("@channel Failed", "thread-ts-123")
    ]
    mock_slack_notify.assert_has_calls(expected_calls)
    mock_update_usage.assert_called_once_with(
        usage_record_id="usage-record-id-123",
        is_completed=False,
        pr_number=None,
        token_input=0,
        token_output=0,
        total_seconds=0,
    )


@pytest.mark.asyncio
async def test_create_pr_from_issue_with_images(
    github_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_datetime,
    mock_slack_notify,
    mock_deconstruct_github_payload,
    mock_delete_comments_by_identifiers,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_render_text,
    mock_is_request_limit_reached,
    mock_create_user_request,
    mock_create_task,
    mock_add_reaction_to_issue,
    mock_get_file_tree_list,
    mock_find_config_files,
    mock_get_remote_file_content,
    mock_get_comments,
    mock_extract_image_urls,
    mock_get_base64,
    mock_describe_image,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_lambda_timeout_approaching,
    mock_check_branch_exists,
    mock_chat_with_agent,
    mock_create_empty_commit,
    mock_create_pull_request,
    mock_pull_request_completed,
    mock_update_usage,
    mock_git_command,
):
    """Test handling of images in issue body and comments."""
    # Setup
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
    mock_extract_image_urls.return_value = [
        {"url": "https://example.com/image1.png", "alt": "Image 1"},
        {"url": "https://example.com/image2.png", "alt": "Image 2"}
    ]
    
    # Execute
    await create_pr_from_issue(github_payload, "issue_comment", "github")
    
    # Verify
    assert mock_get_base64.call_count == 2
    assert mock_describe_image.call_count == 2
    # Should call slack_notify for start and completion
    expected_calls = [
        call("Issue handler started: `issue_comment` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`"),
        call("Completed", "thread-ts-123")
    ]
    mock_slack_notify.assert_has_calls(expected_calls)
    assert mock_create_comment.call_count >= 3  # Initial + 2 image descriptions
        call("PR created for test-owner/test-repo", "thread-ts-123"),


@pytest.mark.asyncio
async def test_create_pr_from_issue_retry_logic(
    github_payload,
    mock_base_args,
    mock_repo_settings,
    mock_time,
    mock_datetime,
    mock_slack_notify,
    mock_deconstruct_github_payload,
    mock_delete_comments_by_identifiers,
    mock_create_progress_bar,
    mock_create_comment,
    mock_update_comment,
    mock_render_text,
    mock_is_request_limit_reached,
    mock_create_user_request,
    mock_create_task,
    mock_add_reaction_to_issue,
    mock_get_file_tree_list,
    mock_find_config_files,
    mock_get_remote_file_content,
    mock_get_comments,
    mock_extract_image_urls,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_lambda_timeout_approaching,
    mock_check_branch_exists,
    mock_chat_with_agent,
    mock_create_empty_commit,
    mock_create_pull_request,
    mock_pull_request_completed,
    mock_update_usage,
    mock_git_command,
):
    """Test retry logic in the main loop."""
    # Setup
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
    
    # Configure chat_with_agent to simulate different scenarios for retry logic
    mock_chat_with_agent.side_effect = [
        # First iteration: is_explored=True, is_committed=False (should increment retry_count)
        (
            [{"role": "user", "content": "test"}],
            ["previous_call_1"],
            "explore",
            {"arg1": "value1"},
            100,
            200,
            True,  # is_explored
            15,
        ),
        (
            [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}],
            ["previous_call_1", "previous_call_2"],
            "commit",
            {"arg2": "value2"},
            150,
            250,
            False,  # is_committed
            25,
        ),
        # Second iteration: is_explored=False, is_committed=True (should increment retry_count)
        (
            [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}, {"role": "user", "content": "follow-up"}],
            ["previous_call_1", "previous_call_2", "previous_call_3"],
            "explore",
            {"arg3": "value3"},
            200,
            300,
            False,  # is_explored
            35,
        ),
        (
            [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}, {"role": "user", "content": "follow-up"}, {"role": "assistant", "content": "final"}],
            ["previous_call_1", "previous_call_2", "previous_call_3", "previous_call_4"],
            "commit",
            {"arg4": "value4"},
            250,
            350,
            True,  # is_committed
            45,
        ),
        # Third iteration: is_explored=True, is_committed=True (should reset retry_count)
        (
            [{"role": "user", "content": "test"}],
            ["previous_call_5"],
            "explore",
            {"arg5": "value5"},
            300,
            400,
            True,  # is_explored
            55,
        ),
        (
            [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}],
            ["previous_call_5", "previous_call_6"],
            "commit",
            {"arg6": "value6"},
            350,
            450,
            True,  # is_committed
            65,
        ),
        # Fourth iteration: is_explored=False, is_committed=False (should break the loop)
        (
            [{"role": "user", "content": "test"}],
            ["previous_call_7"],
            "explore",
            {"arg7": "value7"},
            400,
            500,
            False,  # is_explored
            75,
        ),
        (
            [{"role": "user", "content": "test"}, {"role": "assistant", "content": "response"}],
            ["previous_call_7", "previous_call_8"],
            "commit",
            {"arg8": "value8"},
            450,
            550,
            False,  # is_committed
            85,
        ),
    ]
    
    # Make sure is_lambda_timeout_approaching doesn't interrupt our test
    mock_is_lambda_timeout_approaching.return_value = (False, 10.0)
    
    # Execute
    await create_pr_from_issue(github_payload, "issue_comment", "github")
    
    # Verify
    assert mock_chat_with_agent.call_count == 8  # 4 iterations, 2 calls per iteration
    mock_create_empty_commit.assert_called_once()
    mock_create_pull_request.assert_called_once()
    # Should call slack_notify for start and completion
    expected_calls = [
        call("Issue handler started: `issue_comment` by `test-sender` for `123:Test Issue` in `test-owner/test-repo`"),
        call("Completed", "thread-ts-123")
    ]
    mock_slack_notify.assert_has_calls(expected_calls)

