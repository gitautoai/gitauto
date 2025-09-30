from unittest.mock import Mock, patch
from services.chat_with_agent import chat_with_agent


@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
def test_chat_with_agent_passes_usage_id_to_claude(
    mock_chat_with_claude, mock_get_model
):
    mock_get_model.return_value = "claude-sonnet-4-0"
    mock_chat_with_claude.return_value = (
        {"role": "assistant", "content": "response"},
        None,  # tool_call_id
        None,  # tool_name
        None,  # tool_args
        15,  # token_input
        10,  # token_output
    )

    base_args = Mock()
    repo_settings = None

    chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=base_args,
        mode="explore",
        repo_settings=repo_settings,
        usage_id=123,
    )

    mock_chat_with_claude.assert_called_once()
    call_args = mock_chat_with_claude.call_args[1]
    assert call_args["usage_id"] == 123


@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_openai")
def test_chat_with_agent_passes_usage_id_to_openai(
    mock_chat_with_openai, mock_get_model
):
    mock_get_model.return_value = "gpt-5"
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "response"},
        None,  # tool_call_id
        None,  # tool_name
        None,  # tool_args
        20,  # token_input
        8,  # token_output
    )

    base_args = Mock()
    repo_settings = None

    chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=base_args,
        mode="explore",
        repo_settings=repo_settings,
        usage_id=456,
    )

    mock_chat_with_openai.assert_called_once()
    call_args = mock_chat_with_openai.call_args[1]
    assert call_args["usage_id"] == 456


@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
def test_chat_with_agent_returns_token_counts(mock_chat_with_claude, mock_get_model):
    mock_get_model.return_value = "claude-sonnet-4-0"
    mock_chat_with_claude.return_value = (
        {"role": "assistant", "content": "response"},
        None,
        None,
        None,
        25,  # token_input
        15,  # token_output
    )

    base_args = Mock()

    result = chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        usage_id=789,
    )

    assert result[4] == 25  # token_input
    assert result[5] == 15  # token_output


@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
def test_get_remote_file_content_start_line_end_line_logging(
    mock_update_comment, mock_chat_with_claude, mock_get_model
):
    """Test that start_line and end_line parameters are properly logged in chat_with_agent."""
    mock_get_model.return_value = "claude-sonnet-4-0"
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "get_remote_file_content",
                    "input": {"file_path": "test.py", "start_line": 10, "end_line": 20},
                }
            ],
        },
        "test_id",
        "get_remote_file_content",
        {"file_path": "test.py", "start_line": 10, "end_line": 20},
        15,
        10,
    )

    base_args = Mock()

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(return_value="file content")

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=base_args,
            mode="explore",
            repo_settings=None,
        )

    # Check that update_comment was called with the correct message
    call_args = mock_update_comment.call_args_list
    assert len(call_args) > 0

    # Find the call with our expected message
    found_message = False
    for call in call_args:
        body_arg = call.kwargs.get("body", "")
        if "Read `test.py` lines 10-20." in body_arg:
            found_message = True
            break

    assert (
        found_message
    ), f"Expected message not found in update_comment calls: {[call.kwargs.get('body', '') for call in call_args]}"


@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
def test_delete_file_logging(mock_update_comment, mock_chat_with_claude, mock_get_model):
    """Test that delete_file function calls are properly logged in chat_with_agent."""
    mock_get_model.return_value = "claude-sonnet-4-0"
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
        "test_id",
        "delete_file",
        {"file_path": "test_file.py"},
        15,
        10,
    )

    base_args = Mock()

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(return_value="File deleted successfully")

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=base_args,
            mode="commit",
            repo_settings=None,
        )

    # Check that update_comment was called with the correct message
    call_args = mock_update_comment.call_args_list
    assert len(call_args) > 0

    # Find the call with our expected message
    found_message = False
    for call in call_args:
        body_arg = call.kwargs.get("body", "")
        if "Deleted file `test_file.py`." in body_arg:
            found_message = True
            break

    assert (
        found_message
    ), f"Expected delete message not found in update_comment calls: {[call.kwargs.get('body', '') for call in call_args]}"


@patch("services.chat_with_agent.get_model")
@patch("services.chat_with_agent.chat_with_claude")
@patch("services.chat_with_agent.update_comment")
def test_move_file_logging(mock_update_comment, mock_chat_with_claude, mock_get_model):
    """Test that move_file function calls are properly logged in chat_with_agent."""
    mock_get_model.return_value = "claude-sonnet-4-0"
    mock_chat_with_claude.return_value = (
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test_id",
                    "name": "move_file",
                    "input": {"old_file_path": "old_file.py", "new_file_path": "new_file.py"},
                }
            ],
        },
        "test_id",
        "move_file",
        {"old_file_path": "old_file.py", "new_file_path": "new_file.py"},
        15,
        10,
    )

    base_args = Mock()

    with patch("services.chat_with_agent.tools_to_call") as mock_tools:
        mock_tools.__getitem__.return_value = Mock(return_value="File moved successfully")

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=base_args,
            mode="commit",
            repo_settings=None,
        )

    # Check that update_comment was called with the correct message
    call_args = mock_update_comment.call_args_list
    assert len(call_args) > 0

    # Find the call with our expected message
    found_message = False
    for call in call_args:
        body_arg = call.kwargs.get("body", "")
        if "Moved file from `old_file.py` to `new_file.py`." in body_arg:
            found_message = True
            break

    assert (
        found_message
    ), f"Expected move message not found in update_comment calls: {[call.kwargs.get('body', '') for call in call_args]}"
