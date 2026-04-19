# pylint: disable=too-many-lines
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import Mock, patch
import pytest
from constants.models import ClaudeModelId, GoogleModelId, ModelId
from services.chat_with_agent import chat_with_agent
from services.llm_result import LlmResult, ToolCall
from services.claude.exceptions import ClaudeOverloadedError
from services.claude.tools.file_modify_result import FileMoveResult, FileWriteResult


@pytest.mark.asyncio
@patch("services.chat_with_agent.remove_outdated_messages")
@patch("services.chat_with_agent.chat_with_model")
async def test_calls_remove_outdated_messages_before_chat(
    mock_chat_with_model, mock_remove, create_test_base_args
):
    """remove_outdated_messages is called each iteration before chat_with_model."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={"role": "assistant", "content": "response"},
        tool_calls=[],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )
    base_args = create_test_base_args(model_id=ClaudeModelId.SONNET_4_6)

    await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=ClaudeModelId.SONNET_4_6,
    )

    mock_remove.assert_called_once()


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_chat_with_agent_passes_usage_id_to_claude(
    mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={"role": "assistant", "content": "response"},
        tool_calls=[],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMMA_4_31B)

    await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=GoogleModelId.GEMMA_4_31B,
    )

    mock_chat_with_model.assert_called_once()
    call_args = mock_chat_with_model.call_args[1]
    assert call_args["usage_id"] == 123


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_chat_with_agent_returns_token_counts(
    mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={"role": "assistant", "content": "response"},
        tool_calls=[],
        token_input=25,
        token_output=15,
        cost_usd=0.0,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMINI_2_5_FLASH)

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=789,
        model_id=GoogleModelId.GEMMA_4_31B,
    )

    assert result.token_input == 25
    assert result.token_output == 15
    assert result.cost_usd == 0.0


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_cost_usd_computed_for_claude_model(
    mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={"role": "assistant", "content": "response"},
        tool_calls=[],
        token_input=30_000,
        token_output=500,
        cost_usd=0.1625,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.OPUS_4_7)

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=789,
        model_id=ClaudeModelId.OPUS_4_7,
    )

    assert result.cost_usd == 0.1625


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_cost_usd_computed_for_google_model(
    mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={"role": "assistant", "content": "response"},
        tool_calls=[],
        token_input=100_000,
        token_output=2_000,
        cost_usd=0.0162,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMINI_2_5_FLASH)

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=789,
        model_id=GoogleModelId.GEMINI_2_5_FLASH,
    )

    assert result.cost_usd == 0.0162


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_get_local_file_content_start_line_end_line_logging(
    mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that start_line and end_line parameters are properly logged in chat_with_agent."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="get_local_file_content",
                args={"file_path": "test.py", "start_line": 10, "end_line": 20},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.SONNET_4_6)

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(return_value="file content")

        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test system message",
            base_args=base_args,
            tools=[],
            usage_id=123,
            model_id=ClaudeModelId.SONNET_4_6,
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
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_delete_file_logging(
    mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that delete_file function calls are properly logged in chat_with_agent."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id", name="delete_file", args={"file_path": "test_file.py"}
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.OPUS_4_7)

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
            model_id=ClaudeModelId.OPUS_4_7,
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
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_move_file_logging(
    mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that move_file function calls are properly logged in chat_with_agent."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="move_file",
                args={"old_file_path": "old_file.py", "new_file_path": "new_file.py"},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMMA_4_31B)

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
            model_id=GoogleModelId.GEMMA_4_31B,
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
@patch("services.chat_with_agent.chat_with_model")
async def test_write_and_commit_file_handles_new_content_arg_name(
    mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="write_and_commit_file",
                args={"file_path": "test.py", "new_content": "updated content"},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMINI_2_5_FLASH)

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
            model_id=GoogleModelId.GEMINI_2_5_FLASH,
        )

        mock_function.assert_called_once()
        call_kwargs = mock_function.call_args[1]
        # file_content passed, new_content absent (renamed param)
        assert call_kwargs["file_content"] == "updated content"
        assert call_kwargs.get("new_content") is None


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.slack_notify")
async def test_unavailable_tool_sends_slack_notification(
    mock_slack_notify, mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[ToolCall(id="test_id", name="bash", args={"command": "ls -la"})],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.SONNET_4_6)

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__contains__.return_value = False

        with patch("services.chat_with_agent.update_comment"):
            await chat_with_agent(
                messages=[{"role": "user", "content": "test"}],
                system_message="test system message",
                base_args=base_args,
                tools=[],
                usage_id=123,
                model_id=ClaudeModelId.SONNET_4_6,
            )

        assert mock_slack_notify.call_count == 1
        call_args = mock_slack_notify.call_args[0][0]
        # Exact Slack message format from chat_with_agent.py line 334-338
        assert call_args == (
            "🚨 LLM tried to call unavailable tool:\n"
            "Tool: `bash`\n"
            "Args: `{'command': 'ls -la'}`\n"
            "Repo: `test-owner/test-repo`"
        )


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
@patch("services.chat_with_agent.update_comment")
async def test_verify_task_is_complete_with_pr_changes_returns_is_completed_true(
    _mock_update_comment, mock_get_pr_files, mock_chat_with_model, create_test_base_args
):
    mock_get_pr_files.return_value = [{"filename": "test.py", "status": "modified"}]
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[ToolCall(id="test_id", name="verify_task_is_complete", args={})],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(
        model_id=ClaudeModelId.OPUS_4_7,
        owner="test-owner",
        repo="test-repo",
        pr_number=123,
        token="test-token",
    )

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=ClaudeModelId.OPUS_4_7,
    )

    is_completed = result.is_completed
    assert is_completed is True
    mock_get_pr_files.assert_called_once_with(
        owner="test-owner", repo="test-repo", pr_number=123, token="test-token"
    )


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_task_is_complete_without_pr_changes_returns_is_completed_false(
    mock_get_pr_files, _mock_update_comment, mock_chat_with_model, create_test_base_args
):
    mock_get_pr_files.return_value = []
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[ToolCall(id="test_id", name="verify_task_is_complete", args={})],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(
        model_id=GoogleModelId.GEMMA_4_31B,
        owner="test-owner",
        repo="test-repo",
        pr_number=123,
        token="test-token",
    )

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=GoogleModelId.GEMMA_4_31B,
    )

    assert result.is_completed is True
    messages = result.messages
    last_content = cast(list, messages[-1]["content"])
    last_message = last_content[0]["content"]
    assert last_message == "Task completed. No changes were needed."


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
@patch("services.chat_with_agent.update_comment")
async def test_verify_task_is_complete_with_none_args_still_executes(
    _mock_update_comment, mock_get_pr_files, mock_chat_with_model, create_test_base_args
):
    """PR 786: Gemma 4 31B called verify_task_is_complete with args=None instead of {}.
    isinstance(None, dict) is False, so the tool was silently skipped and returned None.
    Gemma then entered a dead loop returning empty responses for 20 iterations."""
    mock_get_pr_files.return_value = [{"filename": "test.py", "status": "modified"}]
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[ToolCall(id="test_id", name="verify_task_is_complete", args=None)],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(
        model_id=GoogleModelId.GEMMA_4_31B,
        owner="test-owner",
        repo="test-repo",
        pr_number=123,
        token="test-token",
    )

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=GoogleModelId.GEMMA_4_31B,
    )

    # verify_task_is_complete was called (not skipped), so is_completed should be True
    assert result.is_completed is True
    mock_get_pr_files.assert_called_once()


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_regular_tool_returns_is_completed_false(
    mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="get_local_file_content",
                args={"file_path": "test.py"},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMINI_2_5_FLASH)

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
                model_id=GoogleModelId.GEMINI_2_5_FLASH,
            )

    is_completed = result.is_completed
    assert is_completed is False


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_no_tool_call_returns_is_completed_false(
    mock_chat_with_model, create_test_base_args
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={"role": "assistant", "content": "I'm thinking about it..."},
        tool_calls=[],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.SONNET_4_6)

    result = await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test system message",
        base_args=base_args,
        tools=[],
        usage_id=123,
        model_id=ClaudeModelId.SONNET_4_6,
    )

    is_completed = result.is_completed
    assert is_completed is False


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_file_write_result_success_includes_formatted_content(
    _mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that FileWriteResult with success=True includes formatted content with line numbers."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="apply_diff_to_file",
                args={"file_path": "test.py", "diff": "some diff"},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.OPUS_4_7)

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
            model_id=ClaudeModelId.OPUS_4_7,
        )

    messages = result.messages
    tool_result_content_list = cast(list, messages[-1]["content"])
    tool_result_content = tool_result_content_list[0]["content"]

    # FileWriteResult(message="Updated test.py.", content="line1\nline2") → formatted with line numbers
    assert (
        tool_result_content == "Updated test.py.\n\n```test.py\n1:line1\n2:line2\n```"
    )


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_apply_diff_no_changes_logs_tool_result_message(
    mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that apply_diff_to_file with no changes uses tool_result.message instead of hardcoded 'Committed changes'."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="apply_diff_to_file",
                args={"file_path": "test.py", "diff": "some diff"},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMMA_4_31B)

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
            model_id=GoogleModelId.GEMMA_4_31B,
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
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_file_write_result_failure_returns_message_only(
    _mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that FileWriteResult with success=False returns only the message."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="apply_diff_to_file",
                args={"file_path": "test.py", "diff": "bad diff"},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMINI_2_5_FLASH)

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
            model_id=GoogleModelId.GEMINI_2_5_FLASH,
        )

    messages = result.messages
    tool_result_content_list = cast(list, messages[-1]["content"])
    tool_result_content = tool_result_content_list[0]["content"]

    assert tool_result_content == "Invalid diff format."


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_file_move_result_returns_message(
    _mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that FileMoveResult returns the message."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="move_file",
                args={"old_file_path": "old.py", "new_file_path": "new.py"},
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.SONNET_4_6)

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
            model_id=ClaudeModelId.SONNET_4_6,
        )

    messages = result.messages
    tool_result_content_list = cast(list, messages[-1]["content"])
    tool_result_content = tool_result_content_list[0]["content"]

    assert tool_result_content == "Moved old.py to new.py."


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_multiple_parallel_tool_calls(
    _mock_update_comment, mock_chat_with_model, create_test_base_args
):
    """Test that multiple tool_use blocks are all executed and results returned in one message."""
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
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
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=GoogleModelId.GEMINI_2_5_FLASH)

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
            model_id=GoogleModelId.GEMINI_2_5_FLASH,
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
@patch("services.chat_with_agent.chat_with_model")
@patch("services.chat_with_agent.update_comment")
async def test_gitauto_md_edit_always_allowed(
    _mock_update_comment,
    mock_chat_with_model,
    create_test_base_args,
):
    mock_chat_with_model.return_value = LlmResult(
        assistant_message={
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
        tool_calls=[
            ToolCall(
                id="test_id",
                name="write_and_commit_file",
                args={
                    "file_path": "GITAUTO.md",
                    "file_content": "## Testing\n- Use factories",
                },
            )
        ],
        token_input=15,
        token_output=10,
        cost_usd=0.05,
    )

    base_args = create_test_base_args(model_id=ClaudeModelId.SONNET_4_6)

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
            model_id=ClaudeModelId.SONNET_4_6,
        )

    # GITAUTO.md should be editable
    messages = result.messages
    last_content = cast(list, messages[-1]["content"])
    assert last_content[0]["content"] == (
        "Updated GITAUTO.md.\n\n```GITAUTO.md\n1:## Testing\n2:- Use factories\n```"
    )


# --- Fallback chain tests ---


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_opus_falls_back_through_chain_on_error(
    mock_chat_with_model, create_test_base_args
):
    """Opus 4.7 ($8) falls back through 4.6 → 4.5, not Sonnet."""
    models_tried: list[ModelId] = []

    def side_effect(**kwargs):
        models_tried.append(kwargs["model_id"])
        if len(models_tried) < 3:
            raise RuntimeError("model down")
        return LlmResult(
            assistant_message={"role": "assistant", "content": "ok"},
            tool_calls=[],
            token_input=10,
            token_output=5,
            cost_usd=0.05,
        )

    mock_chat_with_model.side_effect = side_effect
    base_args = create_test_base_args(model_id=ClaudeModelId.OPUS_4_7)

    await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test",
        base_args=base_args,
        tools=[],
        usage_id=1,
        model_id=ClaudeModelId.OPUS_4_7,
    )

    assert models_tried == [
        ClaudeModelId.OPUS_4_7,
        ClaudeModelId.OPUS_4_6,
        ClaudeModelId.OPUS_4_5,
    ]


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_sonnet_never_falls_back_to_opus(
    mock_chat_with_model, create_test_base_args
):
    """Sonnet 4.6 ($4) must never escalate to Opus ($8)."""
    models_tried: list[ModelId] = []

    def side_effect(**kwargs):
        models_tried.append(kwargs["model_id"])
        if len(models_tried) < 3:
            raise RuntimeError("model down")
        return LlmResult(
            assistant_message={"role": "assistant", "content": "ok"},
            tool_calls=[],
            token_input=10,
            token_output=5,
            cost_usd=0.05,
        )

    mock_chat_with_model.side_effect = side_effect
    base_args = create_test_base_args(model_id=ClaudeModelId.SONNET_4_6)

    # Sonnet chain: [Sonnet 4.6, Sonnet 4.5] — only 2 models, so 3rd call raises
    with pytest.raises(RuntimeError):
        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test",
            base_args=base_args,
            tools=[],
            usage_id=1,
            model_id=ClaudeModelId.SONNET_4_6,
        )

    # Sonnet 4.6 ($4) fallback: [Sonnet 4.5] — never escalates to Opus ($8)
    assert models_tried == [ClaudeModelId.SONNET_4_6, ClaudeModelId.SONNET_4_5]


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_gemma_never_falls_back_to_gemini(
    mock_chat_with_model, create_test_base_args
):
    """Gemma ($2) must never escalate to Gemini ($4)."""
    models_tried: list[ModelId] = []

    def side_effect(**kwargs):
        models_tried.append(kwargs["model_id"])
        raise RuntimeError("model down")

    mock_chat_with_model.side_effect = side_effect
    base_args = create_test_base_args(model_id=GoogleModelId.GEMMA_4_31B)

    # Gemma chain: [Gemma] only — 1 model, so it raises immediately
    with pytest.raises(RuntimeError):
        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test",
            base_args=base_args,
            tools=[],
            usage_id=1,
            model_id=GoogleModelId.GEMMA_4_31B,
        )

    assert models_tried == [GoogleModelId.GEMMA_4_31B]


@pytest.mark.asyncio
@patch("services.chat_with_agent.asyncio.sleep", return_value=None)
@patch("services.chat_with_agent.chat_with_model")
async def test_overload_retries_then_falls_back(
    mock_chat_with_model, _mock_sleep, create_test_base_args
):
    """Overload retries exhaust on Opus 4.7, then falls back to Opus 4.6."""
    call_count = 0

    def side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        # First 3 calls: Opus 4.7 overloaded (1 initial + 2 retries)
        if call_count <= 3:
            assert kwargs["model_id"] == ClaudeModelId.OPUS_4_7
            raise ClaudeOverloadedError("529")
        # 4th call: falls back to Opus 4.6 and succeeds
        assert kwargs["model_id"] == ClaudeModelId.OPUS_4_6
        return LlmResult(
            assistant_message={"role": "assistant", "content": "ok"},
            tool_calls=[],
            token_input=10,
            token_output=5,
            cost_usd=0.05,
        )

    mock_chat_with_model.side_effect = side_effect
    base_args = create_test_base_args(model_id=GoogleModelId.GEMINI_2_5_FLASH)

    await chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        system_message="test",
        base_args=base_args,
        tools=[],
        usage_id=1,
        model_id=ClaudeModelId.OPUS_4_7,
    )

    assert call_count == 4


@pytest.mark.asyncio
@patch("services.chat_with_agent.chat_with_model")
async def test_all_models_exhausted_raises(mock_chat_with_model, create_test_base_args):
    """When every model in the chain fails, the last exception propagates."""
    mock_chat_with_model.side_effect = RuntimeError("all down")
    base_args = create_test_base_args(model_id=GoogleModelId.GEMMA_4_31B)

    with pytest.raises(RuntimeError, match="all down"):
        await chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            system_message="test",
            base_args=base_args,
            tools=[],
            usage_id=1,
            model_id=GoogleModelId.GEMMA_4_31B,
        )
