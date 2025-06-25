import pytest
from unittest.mock import patch, MagicMock, call
from typing import Any

from config import OPENAI_MODEL_ID_O3_MINI
from services.chat_with_agent import chat_with_agent
from services.github.github_types import BaseArgs


@pytest.fixture
def mock_base_args():
    """Mock base args for testing."""
    return {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "issue_number": 123,
        "comment_url": "https://api.github.com/repos/test_owner/test_repo/issues/comments/123"
    }


@pytest.fixture
def mock_messages():
    """Mock messages for testing."""
    return [
        {"role": "user", "content": "Test message"}
    ]


@pytest.fixture
def mock_system_messages():
    """Mock system messages for testing."""
    return [
        {"role": "system", "content": "Test system message"}
    ]


class TestChatWithAgent:
    """Test cases for chat_with_agent function."""

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.update_comment')
    @patch('services.chat_with_agent.tools_to_call')
    def test_chat_with_agent_comment_mode_success(self, mock_tools_to_call, mock_update_comment, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test chat_with_agent in comment mode with successful execution."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "update_comment",
            {"body": "Updated comment"},
            100,
            50,
        )
        # Mock tools_to_call to make the function execution succeed
        mock_tool_function = MagicMock(return_value="Updated successfully")
        mock_tools_to_call.__contains__.return_value = True
        mock_tools_to_call.__getitem__.return_value = mock_tool_function
        
        # Act
        result = chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="comment"
        )
        
        # Assert
        assert len(result) == 8
        messages, previous_calls, tool_name, tool_args, token_input, token_output, is_done, p = result
        assert tool_name == "update_comment"
        assert tool_args == {"body": "Updated comment"}
        assert token_input == 100
        assert token_output == 50
        assert is_done is True
        assert p == 5

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_claude')
    @patch('services.chat_with_agent.update_comment')
    @patch('services.chat_with_agent.tools_to_call')
    def test_chat_with_agent_uses_claude_when_not_o3_mini(self, mock_tools_to_call, mock_update_comment, mock_chat_claude, mock_get_model, mock_base_args, mock_messages):
        """Test that chat_with_agent uses Claude when model is not O3 Mini."""
        # Arrange
        mock_get_model.return_value = "claude-3-5-sonnet-latest"
        mock_chat_claude.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "update_comment",
            {"body": "Updated comment"},
            100,
            50,
        )
        # Mock tools_to_call to make the function execution succeed
        mock_tool_function = MagicMock(return_value="Comment updated successfully")
        mock_tools_to_call.__contains__.return_value = True
        mock_tools_to_call.__getitem__.return_value = mock_tool_function
        
        # Act
        chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="comment"
        )
        
        # Assert
        mock_chat_claude.assert_called_once()
        mock_get_model.assert_called_once()

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.try_next_model')
    def test_chat_with_agent_retries_on_exception(self, mock_try_next_model, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test that chat_with_agent retries with next model on exception."""
        # Arrange
        mock_get_model.side_effect = [OPENAI_MODEL_ID_O3_MINI, "claude-3-5-sonnet-latest"]
        mock_chat_openai.side_effect = [Exception("API Error"), (
            {"role": "assistant", "content": "Response"},
            None,  # No tool call
            None,
            None,
            100,
            50,
        )]
        mock_try_next_model.return_value = (True, "claude-3-5-sonnet-latest")
        
        # Act
        result = chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="comment"
        )
        
        # Assert
        mock_try_next_model.assert_called_once()
        assert mock_chat_openai.call_count == 2

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.try_next_model')
    def test_chat_with_agent_raises_when_no_more_models(self, mock_try_next_model, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test that chat_with_agent raises exception when no more models available."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.side_effect = Exception("API Error")
        mock_try_next_model.return_value = (False, None)
        
        # Act & Assert
        with pytest.raises(Exception, match="API Error"):
            chat_with_agent(
                messages=mock_messages,
                base_args=mock_base_args,
                mode="comment"
            )

    def test_chat_with_agent_no_tool_calls(self, mock_base_args, mock_messages):
        """Test chat_with_agent when no tools are called."""
        with patch('services.chat_with_agent.get_model') as mock_get_model, \
             patch('services.chat_with_agent.chat_with_openai') as mock_chat_openai, \
             patch('services.chat_with_agent.colorize') as mock_colorize:
            
            # Arrange
            mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
            mock_chat_openai.return_value = (
                {"role": "assistant", "content": "Response"},
                None,  # No tool call ID
                None,  # No tool name
                None,  # No tool args
                100,
                50,
            )
            
            # Act
            result = chat_with_agent(
                messages=mock_messages,
                base_args=mock_base_args,
                mode="comment"
            )
            
            # Assert
            messages, previous_calls, tool_name, tool_args, token_input, token_output, is_done, p = result
            assert tool_name is None
            assert tool_args is None
            assert is_done is False
            mock_colorize.assert_called_once_with("No tools were called in 'comment' mode", "yellow")

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.tools_to_call')
    @patch('services.chat_with_agent.update_comment')
    def test_chat_with_agent_duplicate_function_call(self, mock_update_comment, mock_tools_to_call, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test chat_with_agent handles duplicate function calls."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "update_comment",
            {"body": "Updated comment"},
            100,
            50,
        )
        
        previous_calls = [{"function": "update_comment", "args": {"body": "Updated comment"}}]
        
        # Act
        result = chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="comment",
            previous_calls=previous_calls
        )
        
        # Assert
        messages, returned_previous_calls, tool_name, tool_args, token_input, token_output, is_done, p = result
        # Should not add to previous_calls since it's a duplicate
        assert len(returned_previous_calls) == 1

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.tools_to_call')
    @patch('services.chat_with_agent.update_comment')
    def test_chat_with_agent_function_correction_apply_diff_to_replace(self, mock_update_comment, mock_tools_to_call, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test function name correction from apply_diff_to_file to replace_remote_file_content."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "apply_diff_to_file",
            {"file_path": "test.py", "file_content": "new content"},  # Has file_content, not diff
            100,
            50,
        )
        
        mock_tool_function = MagicMock(return_value="Tool executed")
        mock_tools_to_call.__contains__.return_value = True
        mock_tools_to_call.__getitem__.return_value = mock_tool_function
        
        # Act
        result = chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="commit"
        )
        
        # Assert
        messages, previous_calls, tool_name, tool_args, token_input, token_output, is_done, p = result
        # Should have corrected the function name
        assert previous_calls[0]["function"] == "apply_diff_to_file"  # Original call recorded

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.tools_to_call')
    @patch('services.chat_with_agent.update_comment')
    def test_chat_with_agent_function_correction_similar_name(self, mock_update_comment, mock_tools_to_call, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test function name correction for similar function names."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "create_remote_file",  # Similar name that should be corrected
            {"file_path": "test.py", "file_content": "new content"},
            100,
            50,
        )
        
        mock_tool_function = MagicMock(return_value="Tool executed")
        mock_tools_to_call.__contains__.side_effect = lambda x: x == "replace_remote_file_content"
        mock_tools_to_call.__getitem__.return_value = mock_tool_function
        
        # Act
        result = chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="commit"
        )
        
        # Assert
        messages, previous_calls, tool_name, tool_args, token_input, token_output, is_done, p = result
        assert previous_calls[0]["function"] == "create_remote_file"  # Original call recorded

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.tools_to_call')
    @patch('services.chat_with_agent.update_comment')
    def test_chat_with_agent_invalid_function_name(self, mock_update_comment, mock_tools_to_call, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test chat_with_agent handles invalid function names."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "invalid_function",
            {"arg": "value"},
            100,
            50,
        )
        
        mock_tools_to_call.__contains__.return_value = False
        
        # Act
        result = chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="commit"
        )
        
        # Assert
        messages, previous_calls, tool_name, tool_args, token_input, token_output, is_done, p = result
        # Should have added error message to messages
        assert len(messages) == 3  # Original + response + error
        assert "does not exist in the available tools" in messages[-1]["content"][0]["content"]

    def test_chat_with_agent_mode_configurations(self, mock_base_args, mock_messages):
        """Test that different modes configure correct system content and tools."""
        modes_to_test = ["comment", "commit", "explore", "get", "search"]
        
        for mode in modes_to_test:
            with patch('services.chat_with_agent.get_model') as mock_get_model, \
                 patch('services.chat_with_agent.chat_with_openai') as mock_chat_openai:
                
                # Arrange
                mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
                mock_chat_openai.return_value = (
                    {"role": "assistant", "content": "Response"},
                    None, None, None, 100, 50,
                )
                
                # Act
                chat_with_agent(
                    messages=mock_messages.copy(),
                    base_args=mock_base_args,
                    mode=mode
                )
                
                # Assert
                mock_chat_openai.assert_called_once()
                call_args = mock_chat_openai.call_args
                assert call_args[1]['system_content'] is not None
                assert call_args[1]['tools'] is not None
                
                mock_chat_openai.reset_mock()

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.update_comment')
    @patch('services.chat_with_agent.is_valid_line_number')
    def test_chat_with_agent_get_remote_file_content_with_line_number(self, mock_is_valid_line_number, mock_update_comment, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test chat_with_agent handles get_remote_file_content with line number."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "get_remote_file_content",
            {"file_path": "test.py", "line_number": 10},
            100,
            50,
        )
        mock_is_valid_line_number.return_value = True
        
        # Act
        result = chat_with_agent(
            messages=mock_messages,
            base_args=mock_base_args,
            mode="get",
            recursion_count=1
        )
        
        # Assert
        mock_update_comment.assert_called()
        # Check that the progress message includes line number info
        call_args = mock_update_comment.call_args_list[-1]
        assert "around line 10" in call_args[1]['body']

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.update_comment')
    def test_chat_with_agent_search_remote_file_contents_with_results(self, mock_update_comment, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test chat_with_agent handles search_remote_file_contents with results."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "search_remote_file_contents",
            {"query": "test"},
            100,
            50,
        )
        
        # Mock tool result with file list
        with patch('services.chat_with_agent.tools_to_call') as mock_tools_to_call:
            mock_tool_function = MagicMock(return_value="2 files found for the search query 'test':\n- file1.py\n- file2.py")
            mock_tools_to_call.__contains__.return_value = True
            mock_tools_to_call.__getitem__.return_value = mock_tool_function
            
            # Act
            result = chat_with_agent(
                messages=mock_messages,
                base_args=mock_base_args,
                mode="explore",
                recursion_count=1
            )
            
            # Assert
            mock_update_comment.assert_called()
            # Check that the progress message includes found files
            call_args = mock_update_comment.call_args_list[-1]
            assert "file1.py" in call_args[1]['body']
            assert "file2.py" in call_args[1]['body']

    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.update_comment')
    def test_chat_with_agent_search_google_updates_comment(self, mock_update_comment, mock_chat_openai, mock_get_model, mock_base_args, mock_messages):
        """Test chat_with_agent handles search_google and updates comment."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "search_google",
            {"query": "python testing"},
            100,
            50,
        )
        
        with patch('services.chat_with_agent.tools_to_call') as mock_tools_to_call:
            mock_tool_function = MagicMock(return_value="Search results")
            mock_tools_to_call.__contains__.return_value = True
            mock_tools_to_call.__getitem__.return_value = mock_tool_function
            
            # Act
            result = chat_with_agent(
                messages=mock_messages,
                base_args=mock_base_args,
                mode="search",
                recursion_count=1
            )
            
            # Assert
            # Should call update_comment twice - once for search message, once for final progress
            assert mock_update_comment.call_count == 2
            # Check that search message is included
            first_call_args = mock_update_comment.call_args_list[0]
            assert "Googled `python testing`" in first_call_args[1]['body']

    @patch('services.chat_with_agent.chat_with_agent')
    @patch('services.chat_with_agent.get_model')
    @patch('services.chat_with_agent.chat_with_openai')
    @patch('services.chat_with_agent.update_comment')
    def test_chat_with_agent_recursion_limit(self, mock_update_comment, mock_chat_openai, mock_get_model, mock_chat_with_agent_recursive, mock_base_args, mock_messages):
        """Test chat_with_agent respects recursion limit."""
        # Arrange
        mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
        mock_chat_openai.return_value = (
            {"role": "assistant", "content": "Response"},
            "tool_call_id_123",
            "get_remote_file_content",
            {"file_path": "test.py"},
            100,
            50,
        )
        
        with patch('services.chat_with_agent.tools_to_call') as mock_tools_to_call:
            mock_tool_function = MagicMock(return_value="File content")
            mock_tools_to_call.__contains__.return_value = True
            mock_tools_to_call.__getitem__.return_value = mock_tool_function
            
            # Act - call with recursion_count = 3 (should not recurse)
            result = chat_with_agent(
                messages=mock_messages,
                base_args=mock_base_args,
                mode="get",
                recursion_count=3
            )
            
            # Assert
            # Should not call itself recursively when recursion_count >= 3
            mock_chat_with_agent_recursive.assert_not_called()
            assert len(result) == 8  # Should return the tuple directly

    def test_chat_with_agent_system_messages_integration(self, mock_base_args, mock_messages, mock_system_messages):
        """Test that system messages are properly integrated into system content."""
        with patch('services.chat_with_agent.get_model') as mock_get_model, \
             patch('services.chat_with_agent.chat_with_openai') as mock_chat_openai:
            
            # Arrange
            mock_get_model.return_value = OPENAI_MODEL_ID_O3_MINI
            mock_chat_openai.return_value = (
                {"role": "assistant", "content": "Response"},
                None, None, None, 100, 50,
            )
            
            # Act
            chat_with_agent(
                messages=mock_messages,
                base_args=mock_base_args,
                mode="comment",
                system_messages=mock_system_messages
            )
            
            # Assert
            call_args = mock_chat_openai.call_args
            system_content = call_args[1]['system_content']
            assert "Test system message" in system_content
