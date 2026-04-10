# pylint: disable=too-many-lines
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import Mock, patch
import pytest
from constants.claude import ClaudeModelId
from services.chat_with_agent import chat_with_agent
from services.claude.chat_with_claude import ToolCall
from services.claude.tools.file_modify_result import FileMoveResult, FileWriteResult
from services.types.base_args import BaseArgs


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
async def test_chat_with_agent_passes_usage_id_to_claude(
    mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {"role": "assistant", "content": "response"},
        [],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=None,
    )

    mock_chat_with_claude.assert_called_once()
    call_args = mock_chat_with_claude.call_args[1]
    assert call_args["usage_id"] == 123


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
async def test_chat_with_agent_returns_token_counts(
    mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {"role": "assistant", "content": "response"},
        [],
        25,
        15,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=789,
        model_id=None,
    )

    assert result.token_input == 25
    assert result.token_output == 15


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_get_local_file_content_start_line_end_line_logging(
    mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that start_line and end_line parameters are properly logged in chat_with_agent."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "get_local_file_content",
                    "input": {"file_path": "test.py", "start_line": 10, "end_line": 20},
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="get_local_file_content",
                args={"file_path": "test.py", "start_line": 10, "end_line": 20},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(return_value="file content")

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    call_args = mock_update_comment.call_args_list
    assert len(call_args) > 0

    found_message = False
    for call in call_args:
        body_arg = call.kwargs.get("body", "")
        if "Read `test.py` lines 10-20." in body_arg:
            found_message = True
            break

    assert (
        found_message
    ), f"Expected message not found in update_comment calls: {[call.kwargs.get('body', '') for call in call_args]}"


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_delete_file_logging(
    mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that delete_file function calls are properly logged in chat_with_agent."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "delete_file",
                    "input": {"file_path": "test_file.py"},
                }
            ],
        },
        [
            ToolCall(
                id="test_id", name="delete_file", args={"file_path": "test_file.py"}
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(
            return_value="File deleted successfully"
        )

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    call_args = mock_update_comment.call_args_list
    assert len(call_args) > 0

    found_message = False
    for call in call_args:
        body_arg = call.kwargs.get("body", "")
        if "Deleted file `test_file.py`." in body_arg:
            found_message = True
            break

    assert (
        found_message
    ), f"Expected delete message not found in update_comment calls: {[call.kwargs.get('body', '') for call in call_args]}"


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_move_file_logging(
    mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that move_file function calls are properly logged in chat_with_agent."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "move_file",
                    "input": {
                        "old_file_path": "old_file.py",
                        "new_file_path": "new_file.py",
                    },
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="move_file",
                args={"old_file_path": "old_file.py", "new_file_path": "new_file.py"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(
            return_value="File moved successfully"
        )

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    call_args = mock_update_comment.call_args_list
    assert len(call_args) > 0

    found_message = False
    for call in call_args:
        body_arg = call.kwargs.get("body", "")
        if "Moved file from `old_file.py` to `new_file.py`." in body_arg:
            found_message = True
            break

    assert (
        found_message
    ), f"Expected move message not found in update_comment calls: {[call.kwargs.get('body', '') for call in call_args]}"


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
async def test_write_and_commit_file_handles_new_content_arg_name(
    mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "write_and_commit_file",
                    "input": {
                        "file_path": "test.py",
                        "new_content": "updated content",
                    },
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="write_and_commit_file",
                args={"file_path": "test.py", "new_content": "updated content"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_function = Mock(return_value="Content replaced successfully")
        mock_tools.__getitem__.return_value = mock_function
        mock_tools.__contains__.return_value = True

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

        mock_function.assert_called_once()
        call_kwargs = mock_function.call_args[1]
        assert "file_content" in call_kwargs
        assert call_kwargs["file_content"] == "updated content"
        assert "new_content" not in call_kwargs


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.slack_notify")
async def test_unavailable_tool_sends_slack_notification(
    mock_slack_notify, mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "bash",
                    "input": {"command": "ls -la"},
                }
            ],
        },
        [ToolCall(id="test_id", name="bash", args={"command": "ls -la"})],
        15,
        10,
    )

    base_args = cast(
        BaseArgs,
        {
            "sender_id": 1,
            "sender_name": "test-user",
            "owner": "test-owner",
            "repo": "test-repo",
        },
    )

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__contains__.return_value = False

        with patch("services.chat_with_agent.update_comment"):
            await chat_with_agent(
                messages=[{"role": "user", "content": "test"}],
                system_message="test system message",
                base_args=base_args,
                tools=[],
                usage_id=123,
                model_id=None,
            )

        assert mock_slack_notify.call_count == 1
        call_args = mock_slack_notify.call_args[0][0]
        assert "bash" in call_args
        assert "command" in call_args
        assert "test-owner/test-repo" in call_args


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
@patch("services.chat_with_agent.update_comment")
async def test_verify_task_is_complete_with_pr_changes_returns_is_completed_true(
    _mock_update_comment, mock_get_pr_files, mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_get_pr_files.return_value = [{"filename": "test.py", "status": "modified"}]
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "verify_task_is_complete",
                    "input": {},
                }
            ],
        },
        [ToolCall(id="test_id", name="verify_task_is_complete", args={})],
        15,
        10,
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "sender_id": 1,
            "sender_name": "test-user",
            "verify_consecutive_failures": 0,
            "quality_gate_fail_count": 0,
        },
    )

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=None,
    )

    is_completed = result.is_completed
    assert is_completed is True
    mock_get_pr_files.assert_called_once_with(
        owner="test-owner", repo="test-repo", pr_number=123, token="test-token"
    )


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_task_is_complete_without_pr_changes_returns_is_completed_false(
    mock_get_pr_files, _mock_update_comment, mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_get_pr_files.return_value = []
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "verify_task_is_complete",
                    "input": {},
                }
            ],
        },
        [ToolCall(id="test_id", name="verify_task_is_complete", args={})],
        15,
        10,
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "sender_id": 1,
            "sender_name": "test-user",
            "verify_consecutive_failures": 0,
            "quality_gate_fail_count": 0,
        },
    )

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=None,
    )

    assert result.is_completed is True
    messages = result.messages
    last_content = cast(list, messages[-1]["content"])
    last_message = last_content[0]["content"]
    assert "No changes were needed" in last_message


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
async def test_regular_tool_returns_is_completed_false(
    mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "get_local_file_content",
                    "input": {"file_path": "test.py"},
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="get_local_file_content",
                args={"file_path": "test.py"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(return_value="file content")
        mock_tools.__contains__.return_value = True

        with patch("services.chat_with_agent.update_comment"):
            result = await chat_with_agent(
                messages=[{"role": "user", "content": "test"}],
                system_message="test system message",
                base_args=base_args,
                tools=[],
                usage_id=123,
                model_id=None,
            )

    is_completed = result.is_completed
    assert is_completed is False


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
async def test_no_tool_call_returns_is_completed_false(
    mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {"role": "assistant", "content": "I'm thinking about it..."},
        [],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=None,
    )

    is_completed = result.is_completed
    assert is_completed is False


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_file_write_result_success_includes_formatted_content(
    _mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that FileWriteResult with success=True includes formatted content with line numbers."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "test.py", "diff": "some diff"},
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="apply_diff_to_file",
                args={"file_path": "test.py", "diff": "some diff"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__contains__.return_value = True
        mock_tools.__getitem__.return_value = Mock(
            return_value=FileWriteResult(
                success=True,
                message="Updated test.py.",
                file_path="test.py",
                content="line1\nline2",
            )
        )

        result = await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    messages = result.messages
    tool_result_content_list = cast(list, messages[-1]["content"])
    tool_result_content = tool_result_content_list[0]["content"]

    assert "Updated test.py." in tool_result_content
    assert "```test.py" in tool_result_content
    assert "1:line1" in tool_result_content
    assert "2:line2" in tool_result_content


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_apply_diff_no_changes_logs_tool_result_message(
    mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that apply_diff_to_file with no changes uses tool_result.message instead of hardcoded 'Committed changes'."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "test.py", "diff": "some diff"},
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="apply_diff_to_file",
                args={"file_path": "test.py", "diff": "some diff"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__contains__.return_value = True
        mock_tools.__getitem__.return_value = Mock(
            return_value=FileWriteResult(
                success=False,
                message="No changes to test.py.",
                file_path="test.py",
                content="original content",
            )
        )

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    call_args = mock_update_comment.call_args_list
    assert len(call_args) > 0

    found_no_changes = False
    found_committed = False
    for call in call_args:
        body_arg = call.kwargs.get("body", "")
        if "No changes to test.py." in body_arg:
            found_no_changes = True
        if "Committed changes" in body_arg:
            found_committed = True

    assert (
        found_no_changes
    ), f"Expected 'No changes to test.py.' in update_comment calls: {[call.kwargs.get('body', '') for call in call_args]}"
    assert (
        not found_committed
    ), f"Should not contain 'Committed changes' when there are no changes: {[call.kwargs.get('body', '') for call in call_args]}"


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_file_write_result_failure_returns_message_only(
    _mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that FileWriteResult with success=False returns only the message."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "test.py", "diff": "bad diff"},
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="apply_diff_to_file",
                args={"file_path": "test.py", "diff": "bad diff"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__contains__.return_value = True
        mock_tools.__getitem__.return_value = Mock(
            return_value=FileWriteResult(
                success=False,
                message="Invalid diff format.",
                file_path="test.py",
                content="original content",
            )
        )

        result = await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    messages = result.messages
    tool_result_content_list = cast(list, messages[-1]["content"])
    tool_result_content = tool_result_content_list[0]["content"]

    assert tool_result_content == "Invalid diff format."


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_file_move_result_returns_message(
    _mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that FileMoveResult returns the message."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "move_file",
                    "input": {
                        "old_file_path": "old.py",
                        "new_file_path": "new.py",
                    },
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="move_file",
                args={"old_file_path": "old.py", "new_file_path": "new.py"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__contains__.return_value = True
        mock_tools.__getitem__.return_value = Mock(
            return_value=FileMoveResult(
                success=True,
                message="Moved old.py to new.py.",
                old_file_path="old.py",
                new_file_path="new.py",
            )
        )

        result = await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    messages = result.messages
    tool_result_content_list = cast(list, messages[-1]["content"])
    tool_result_content = tool_result_content_list[0]["content"]

    assert tool_result_content == "Moved old.py to new.py."


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
@patch("services.chat_with_agent.replace_old_file_content")
async def test_full_file_read_calls_replace_with_is_full_file_read_true(
    mock_replace, _mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that reading a full file calls replace_old_file_content with is_full_file_read=True."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "get_local_file_content",
                    "input": {"file_path": "src/main.py"},
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="get_local_file_content",
                args={"file_path": "src/main.py"},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(
            return_value="```src/main.py\n1:print('hello')\n```"
        )
        mock_tools.__contains__.return_value = True

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    mock_replace.assert_called_once()
    call_args = mock_replace.call_args
    assert call_args[0][1] == "src/main.py"
    assert call_args[1]["is_full_file_read"] is True


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
@patch("services.chat_with_agent.replace_old_file_content")
async def test_partial_file_read_calls_replace_with_is_full_file_read_false(
    mock_replace, _mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that reading a partial file calls replace_old_file_content with is_full_file_read=False."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "get_local_file_content",
                    "input": {
                        "file_path": "src/main.py",
                        "start_line": 10,
                        "end_line": 20,
                    },
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="get_local_file_content",
                args={"file_path": "src/main.py", "start_line": 10, "end_line": 20},
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(
            return_value="```src/main.py#L10-L20\n10:code here\n```"
        )
        mock_tools.__contains__.return_value = True

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    mock_replace.assert_called_once()
    call_args = mock_replace.call_args
    assert call_args[0][1] == "src/main.py#L10-L20"
    assert call_args[1]["is_full_file_read"] is False


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_multiple_parallel_tool_calls(
    _mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that multiple tool_use blocks are all executed and results returned in one message."""
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_1",
                    "name": "get_local_file_content",
                    "input": {"file_path": "a.py"},
                },
                {
                    "type": "tool_use",
                    "id": "tool_2",
                    "name": "get_local_file_content",
                    "input": {"file_path": "b.py"},
                },
                {
                    "type": "tool_use",
                    "id": "tool_3",
                    "name": "get_local_file_content",
                    "input": {"file_path": "c.py"},
                },
            ],
        },
        [
            ToolCall(
                id="tool_1", name="get_local_file_content", args={"file_path": "a.py"}
            ),
            ToolCall(
                id="tool_2", name="get_local_file_content", args={"file_path": "b.py"}
            ),
            ToolCall(
                id="tool_3", name="get_local_file_content", args={"file_path": "c.py"}
            ),
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        call_count = 0

        def mock_tool_fn(**kwargs):
            nonlocal call_count
            call_count += 1
            return f"content of {kwargs['file_path']}"

        mock_tools.__getitem__.return_value = mock_tool_fn
        mock_tools.__contains__.return_value = True

        result = await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    # All 3 tools were executed
    assert call_count == 3

    # Last message contains 3 tool_result blocks
    messages = result.messages
    last_content = cast(list, messages[-1]["content"])
    assert len(last_content) == 3
    assert last_content[0]["tool_use_id"] == "tool_1"
    assert last_content[1]["tool_use_id"] == "tool_2"
    assert last_content[2]["tool_use_id"] == "tool_3"

    # Progress reflects all 3 tool calls
    assert result.p == 15  # 5 * 3


@pytest.mark.asyncio
@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
async def test_gitauto_md_edit_always_allowed(
    _mock_update_comment,
    mock_chat_with_claude,
    mock_get_model,
):
    mock_get_model.return_value = ClaudeModelId.SONNET_4_6
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "write_and_commit_file",
                    "input": {
                        "file_path": "GITAUTO.md",
                        "file_content": "## Testing\n- Use factories",
                    },
                }
            ],
        },
        [
            ToolCall(
                id="test_id",
                name="write_and_commit_file",
                args={
                    "file_path": "GITAUTO.md",
                    "file_content": "## Testing\n- Use factories",
                },
            )
        ],
        15,
        10,
    )

    base_args = cast(BaseArgs, {"sender_id": 1, "sender_name": "test-user"})

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__contains__.return_value = True
        mock_tools.__getitem__.return_value = Mock(
            return_value=FileWriteResult(
                success=True,
                message="Updated GITAUTO.md.",
                file_path="GITAUTO.md",
                content="## Testing\n- Use factories",
            )
        )

        result = await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=None,
        )

    # GITAUTO.md should be editable
    messages = result.messages
    last_content = cast(list, messages[-1]["content"])
    assert "Updated GITAUTO.md." in last_content[0]["content"]
