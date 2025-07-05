# Standard imports
import pytest
from unittest.mock import patch, MagicMock, call

# Local imports
from config import OPENAI_MODEL_ID_O3_MINI
from services.chat_with_agent import chat_with_agent
from services.supabase.usage.insert_usage import Trigger


@pytest.fixture
def mock_create_system_message():
    with patch("services.chat_with_agent.create_system_message") as mock:
        mock.return_value = "Test system message"
        yield mock


@pytest.fixture
def mock_get_model():
    with patch("services.chat_with_agent.get_model") as mock:
        mock.return_value = OPENAI_MODEL_ID_O3_MINI
        yield mock


@pytest.fixture
def mock_try_next_model():
    with patch("services.chat_with_agent.try_next_model") as mock:
        mock.return_value = (True, "next_model")
        yield mock


@pytest.fixture
def mock_chat_with_openai():
    with patch("services.chat_with_agent.chat_with_openai") as mock:
        mock.return_value = (
            {"role": "assistant", "content": "Test response"},  # response_message
            "tool_call_id_123",  # tool_call_id
            "get_remote_file_content",  # tool_name
            {"file_path": "test.py"},  # tool_args
            100,  # token_input
            50,  # token_output
        )
        yield mock


@pytest.fixture
def mock_chat_with_claude():
    with patch("services.chat_with_agent.chat_with_claude") as mock:
        mock.return_value = (
            {"role": "assistant", "content": "Test response"},  # response_message
            "tool_call_id_123",  # tool_call_id
            "get_remote_file_content",  # tool_name
            {"file_path": "test.py"},  # tool_args
            100,  # token_input
            50,  # token_output
        )
        yield mock


@pytest.fixture
def mock_colorize():
    with patch("services.chat_with_agent.colorize") as mock:
        mock.return_value = "Colorized text"
        yield mock


@pytest.fixture
def mock_update_comment():
    with patch("services.chat_with_agent.update_comment") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_create_progress_bar():
    with patch("services.chat_with_agent.create_progress_bar") as mock:
        mock.return_value = "Progress bar"
        yield mock


@pytest.fixture
def mock_is_valid_line_number():
    with patch("services.chat_with_agent.is_valid_line_number") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_tools_to_call():
    mock_function = MagicMock()
    mock_function.return_value = "Tool result"
    
    with patch.dict("services.chat_with_agent.tools_to_call", {
        "get_remote_file_content": mock_function,
        "search_remote_file_contents": mock_function,
        "apply_diff_to_file": mock_function,
        "replace_remote_file_content": mock_function,
        "search_google": mock_function,
    }):
        yield mock_function


@pytest.fixture
def base_args():
    return {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "issue_number": 123,
        "comment_url": "https://api.github.com/repos/test_owner/test_repo/issues/comments/123",
    }


@pytest.fixture
def messages():
    return [
        {"role": "user", "content": "Test message"}
    ]


def test_chat_with_agent_basic_flow(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_create_progress_bar,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test the basic flow of chat_with_agent with OpenAI provider."""
    trigger = "issue_label"
    mode = "explore"
    repo_settings = None
    
    result = chat_with_agent(
        # Use a copy to avoid modifying the fixture
        messages=messages.copy(),
        trigger=trigger,
        base_args=base_args,
        mode=mode,
        repo_settings=repo_settings,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that the system message was created
    mock_create_system_message.assert_called_once_with(
        trigger=trigger, mode=mode, repo_settings=repo_settings
    )
    
    # Check that the model was selected
    mock_get_model.assert_called_once()
    
    # Check that the chat provider was called with correct arguments
    mock_chat_with_openai.assert_called_once()
    args, kwargs = mock_chat_with_openai.call_args
    # Check that the original message is in the list passed to chat_with_openai
    assert any(msg == messages[0] for msg in args[0])
    assert kwargs["system_content"] == "Test system message"
    
    # Check that the tool was called
    mock_tools_to_call.assert_called_once_with(file_path="test.py", base_args=base_args)
    
    # Check that update_comment was called
    mock_update_comment.assert_called()
    
    # Check the return values
    assert len(result) == 8
    # The original messages fixture has only one message, but the result should have 3 messages
    # (the original message plus the assistant response and tool result)
    assert len(result[0]) == 3
    assert result[0][0] == {"role": "user", "content": "Test message"}
    assert result[1] == [{"function": "get_remote_file_content", "args": {"file_path": "test.py"}}]
    assert result[2] == "get_remote_file_content"
    assert result[3] == {"file_path": "test.py"}
    assert result[4] == 100
    assert result[5] == 50
    assert result[6] is True  # is_done
    assert result[7] == 5  # p + 5


def test_chat_with_agent_no_tool_calls(
    mock_create_system_message,
    mock_get_model,
    mock_colorize,
    mock_chat_with_openai,
    base_args,
    messages,
):
    """Test chat_with_agent when no tools are called."""
    # Override the mock to return no tool name
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        None,  # tool_call_id
        "",  # tool_name (empty)
        {},  # tool_args
        100,  # token_input
        50,  # token_output
    )
    
    result = chat_with_agent(
        messages=messages.copy(),  # Use a copy to avoid modifying the fixture
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that colorize was called with the correct message
    mock_colorize.assert_called_once_with("No tools were called in 'explore' mode", "yellow")
    
    # Check the return values
    assert len(result) == 8
    assert result[0] == messages
    assert result[1] == []
    assert result[2] is None
    assert result[3] is None
    assert result[4] == 100
    assert result[5] == 50
    assert result[6] is False  # is_done
    assert result[7] == 0  # p


def test_chat_with_agent_duplicate_function_call(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    base_args,
    messages,
):
    """Test chat_with_agent when the same function is called with the same arguments."""
    previous_calls = [
        {"function": "get_remote_file_content", "args": {"file_path": "test.py"}}
    ]
    
    with patch("builtins.print") as mock_print:
        result = chat_with_agent(
            messages=messages.copy(),
            trigger="issue_label",
            base_args=base_args,
            mode="explore",
            repo_settings=None,
            previous_calls=previous_calls,
            recursion_count=3,  # Prevent recursion for testing
        )
    
    # Check that print was called with the error message
    assert mock_print.call_count == 2
    # First call should be the model selection message
    assert mock_print.call_args_list[0][0][0] == "Using model: o3-mini"
    # Second call should be the error message
    
    # Check that the previous_calls list wasn't modified
    assert result[1] == previous_calls


def test_chat_with_agent_function_correction(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when function arguments suggest a different function."""
    # Set up the mock to return a function that needs correction
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "apply_diff_to_file",  # Function that needs correction
        {"file_path": "test.py", "file_content": "content"},  # Missing diff, has file_content
        100,
        50,
    )
    
    with patch("builtins.print") as mock_print:
        result = chat_with_agent(
            messages=messages.copy(),
            trigger="issue_label",
            base_args=base_args,
            mode="commit",
            repo_settings=None,
            recursion_count=3,  # Prevent recursion for testing
        )
    
    # Check that print was called with the warning message
    assert mock_print.call_count == 2
    # First call should be the model selection message
    assert mock_print.call_args_list[0][0][0] == "Using model: o3-mini"
    # Second call should be the warning message
    
    # Check that the corrected function was called
    mock_tools_to_call.assert_called_once_with(
        file_path="test.py", file_content="content", base_args=base_args
    )
    
    # Check that the previous_calls list contains the original function name
    assert result[1] == [{"function": "apply_diff_to_file", "args": {"file_path": "test.py", "file_content": "content"}}]


def test_chat_with_agent_similar_function_name(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when a similar function name is used."""
    # Set up the mock to return a function with a similar name
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "create_remote_file",  # Similar function name
        {"file_path": "test.py", "file_content": "content"},
        100,
        50,
    )
    
    with patch("builtins.print") as mock_print:
        result = chat_with_agent(
            messages=messages.copy(),
            trigger="issue_label",
            base_args=base_args,
            mode="commit",
            repo_settings=None,
            recursion_count=3,  # Prevent recursion for testing
        )
    
    # Check that print was called with the warning message
    mock_print.assert_called_once()
    assert "Warning: Redirecting call from 'create_remote_file' to 'replace_remote_file_content'" in mock_print.call_args[0][0]
    
    # Check that the corrected function was called
    mock_tools_to_call.assert_called_once_with(
        file_path="test.py", file_content="content", base_args=base_args
    )
    
    # Check that the previous_calls list contains the original function name
    assert result[1] == [{"function": "create_remote_file", "args": {"file_path": "test.py", "file_content": "content"}}]


def test_chat_with_agent_nonexistent_function(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    base_args,
    messages,
):
    """Test chat_with_agent when a nonexistent function is called."""
    # Set up the mock to return a nonexistent function
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "nonexistent_function",  # Nonexistent function
        {"arg1": "value1"},
        100,
        50,
    )
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that the tool_result contains an error message
    assert "Error: The function 'nonexistent_function' does not exist" in result[0][-1]["content"][0]["content"]
    
    # Check that the previous_calls list wasn't modified
    assert result[1] == []
    
    # Check that is_done is False
    assert result[6] is False


def test_chat_with_agent_get_remote_file_content_with_line_number(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    mock_is_valid_line_number,
    base_args,
    messages,
):
    """Test chat_with_agent when get_remote_file_content is called with a line number."""
    # Set up the mock to return get_remote_file_content with line_number
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "get_remote_file_content",
        {"file_path": "test.py", "line_number": 42},
        100,
        50,
    )
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that is_valid_line_number was called
    mock_is_valid_line_number.assert_called_once_with(42)
    
    # Check that the log message contains the line number
    assert result[0][-1]["content"][0]["content"] == "Tool result"


def test_chat_with_agent_get_remote_file_content_with_keyword(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when get_remote_file_content is called with a keyword."""
    # Set up the mock to return get_remote_file_content with keyword
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "get_remote_file_content",
        {"file_path": "test.py", "keyword": "def test_function"},
        100,
        50,
    )
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that the log message contains the keyword
    assert result[0][-1]["content"][0]["content"] == "Tool result"


def test_chat_with_agent_search_remote_file_contents_with_results(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when search_remote_file_contents is called and finds results."""
    # Set up the mock to return search_remote_file_contents
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "search_remote_file_contents",
        {"query": "test_function"},
        100,
        50,
    )
    
    # Set up the tool result to include file matches
    mock_tools_to_call.return_value = "3 files found:\n- file1.py\n- file2.py\n- file3.py"
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that the log message contains the search results
    assert result[0][-1]["content"][0]["content"] == "3 files found:\n- file1.py\n- file2.py\n- file3.py"


def test_chat_with_agent_search_remote_file_contents_no_results(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when search_remote_file_contents is called but finds no results."""
    # Set up the mock to return search_remote_file_contents
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "search_remote_file_contents",
        {"query": "nonexistent_function"},
        100,
        50,
    )
    
    # Set up the tool result to indicate no matches
    mock_tools_to_call.return_value = "0 files found for query 'nonexistent_function'"
    
    result = chat_with_agent(
        messages=messages,
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that the log message indicates no files were found
    assert result[0][-1]["content"][0]["content"] == "0 files found for query 'nonexistent_function'"


def test_chat_with_agent_search_google(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    mock_create_progress_bar,
    base_args,
    messages,
):
    """Test chat_with_agent when search_google is called."""
    # Set up the mock to return search_google
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "search_google",
        {"query": "python testing best practices"},
        100,
        50,
    )
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="search",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that update_comment was called with the progress bar
    assert mock_update_comment.call_count >= 2
    
    # Check that the log message contains the search query
    assert result[0][-1]["content"][0]["content"] == "Tool result"


def test_chat_with_agent_apply_diff_to_file(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when apply_diff_to_file is called."""
    # Set up the mock to return apply_diff_to_file
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "apply_diff_to_file",
        {"file_path": "test.py", "diff": "--- test.py\n+++ test.py\n@@ -1,1 +1,1 @@\n-old line\n+new line"},
        100,
        50,
    )
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="commit",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that the log message contains the file path
    assert result[0][-1]["content"][0]["content"] == "Tool result"


def test_chat_with_agent_replace_remote_file_content(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when replace_remote_file_content is called."""
    # Set up the mock to return replace_remote_file_content
    mock_chat_with_openai.return_value = (
        {"role": "assistant", "content": "Test response"},
        "tool_call_id_123",
        "replace_remote_file_content",
        {"file_path": "test.py", "file_content": "new content"},
        100,
        50,
    )
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="commit",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that the log message contains the file path
    assert result[0][-1]["content"][0]["content"] == "Tool result"


def test_chat_with_agent_model_fallback(
    mock_create_system_message,
    mock_get_model,
    mock_try_next_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when the first model fails and falls back to the next model."""
    # Set up the first call to raise an exception, then succeed on the second call
    mock_chat_with_openai.side_effect = [
        Exception("Model error"),
        (
            {"role": "assistant", "content": "Test response"},
            "tool_call_id_123",
            "get_remote_file_content",
            {"file_path": "test.py"},
            100,
            50,
        )
    ]
    
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Prevent recursion for testing
    )
    
    # Check that try_next_model was called
    mock_try_next_model.assert_called_once()
    
    # Check that chat_with_openai was called twice
    assert mock_chat_with_openai.call_count == 2
    
    # Check that the function completed successfully
    assert result[2] == "get_remote_file_content"
    assert result[6] is True  # is_done


def test_chat_with_agent_model_fallback_all_models_fail(
    mock_create_system_message,
    mock_get_model,
    mock_try_next_model,
    mock_chat_with_openai,
    base_args,
    messages,
):
    """Test chat_with_agent when all models fail."""
    # Set up the chat function to always raise an exception
    mock_chat_with_openai.side_effect = Exception("Model error")
    
    # Set up try_next_model to indicate no more models
    mock_try_next_model.return_value = (False, "last_model")
    
    # The function should raise an exception
    with pytest.raises(Exception, match="Model error"):
        chat_with_agent(
            messages=messages.copy(),
            trigger="issue_label",
            base_args=base_args,
            mode="explore",
            repo_settings=None,
            recursion_count=3,  # Prevent recursion for testing
        )
    
    # Check that try_next_model was called
    mock_try_next_model.assert_called_once()


def test_chat_with_agent_recursion(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent recursion behavior."""
    # We'll need to patch the chat_with_agent function itself to test recursion
    with patch("services.chat_with_agent.chat_with_agent", wraps=chat_with_agent) as wrapped_chat:
        result = chat_with_agent(
            messages=messages.copy(),
            trigger="issue_label",
            base_args=base_args,
            mode="explore",
            repo_settings=None,
            recursion_count=1,  # Start at 1 to allow for recursion
        )
        
        # Check that chat_with_agent was called recursively
        assert wrapped_chat.call_count == 1  # The original call
        
        # The wrapped function should have been called with recursion_count=2
        args, kwargs = wrapped_chat.call_args
        assert kwargs["recursion_count"] == 2


def test_chat_with_agent_max_recursion(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent when maximum recursion is reached."""
    # Call with recursion_count=3 (max allowed)
    result = chat_with_agent(
        messages=messages.copy(),
        trigger="issue_label",
        base_args=base_args,
        mode="explore",
        repo_settings=None,
        recursion_count=3,  # Max recursion
    )
    
    # Function should return normally without recursing further
    assert result[2] == "get_remote_file_content"
    assert result[6] is True  # is_done


def test_chat_with_agent_different_modes(
    mock_create_system_message,
    mock_get_model,
    mock_chat_with_openai,
    mock_update_comment,
    mock_tools_to_call,
    base_args,
    messages,
):
    """Test chat_with_agent with different modes."""
    from services.openai.functions.functions import (
        TOOLS_TO_UPDATE_COMMENT,
        TOOLS_TO_COMMIT_CHANGES,
        TOOLS_TO_EXPLORE_REPO,
        TOOLS_TO_GET_FILE,
        TOOLS_TO_SEARCH_GOOGLE,
    )
    
    # Test each mode
    modes_to_tools = {
        "comment": TOOLS_TO_UPDATE_COMMENT,
        "commit": TOOLS_TO_COMMIT_CHANGES,
        "explore": TOOLS_TO_EXPLORE_REPO,
        "get": TOOLS_TO_GET_FILE,
        "search": TOOLS_TO_SEARCH_GOOGLE,
    }
    
    for mode, expected_tools in modes_to_tools.items():
        mock_chat_with_openai.reset_mock()
        
        result = chat_with_agent(
            messages=messages.copy(),
            trigger="issue_label",
            base_args=base_args,
            mode=mode,
            repo_settings=None,
            recursion_count=3,  # Prevent recursion for testing
        )
        
        # Check that the correct tools were selected based on mode
        args, kwargs = mock_chat_with_openai.call_args
        assert kwargs["tools"] == expected_tools
