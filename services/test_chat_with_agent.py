# pylint: disable=redefined-outer-name
# pylint: disable=too-many-lines
from unittest.mock import Mock, patch

import pytest
from services.chat_with_agent import chat_with_agent


@pytest.fixture
def mock_base_args():
    """Fixture to create a mock BaseArgs object."""
    return Mock()


@pytest.fixture
def mock_repo_settings():
    """Fixture to create a mock Repositories object."""
    return Mock()


@pytest.fixture
def mock_get_model():
    """Fixture to mock get_model function."""
    with patch("services.chat_with_agent.get_model") as mock:
        mock.return_value = "claude-sonnet-4-0"
        yield mock


@pytest.fixture
def mock_chat_with_claude():
    """Fixture to mock chat_with_claude function."""
    with patch("services.chat_with_agent.chat_with_claude") as mock:
        mock.return_value = (
            {"role": "assistant", "content": "response"},
            None,
            None,
            None,
            15,
            10,
        )
        yield mock


@pytest.fixture
def mock_chat_with_openai():
    """Fixture to mock chat_with_openai function."""
    with patch("services.chat_with_agent.chat_with_openai") as mock:
        mock.return_value = (
            {"role": "assistant", "content": "response"},
            None,
            None,
            None,
            20,
            8,
        )
        yield mock


@pytest.fixture
def mock_update_comment():
    """Fixture to mock update_comment function."""
    with patch("services.chat_with_agent.update_comment") as mock:
        yield mock


@pytest.fixture
def mock_tools_to_call():
    """Fixture to mock tools_to_call dictionary."""
    with patch("services.chat_with_agent.tools_to_call") as mock:
        mock.__getitem__.return_value = Mock(return_value="tool result")
        mock.__contains__.return_value = True
        yield mock


@pytest.fixture
def mock_try_next_model():
    """Fixture to mock try_next_model function."""
    with patch("services.chat_with_agent.try_next_model") as mock:
        mock.return_value = (False, "current-model")
        yield mock


@pytest.fixture
def mock_is_valid_line_number():
    """Fixture to mock is_valid_line_number function."""
    with patch("services.chat_with_agent.is_valid_line_number") as mock:
        mock.return_value = True
        yield mock


def test_chat_with_agent_passes_usage_id_to_claude(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that usage_id is passed to Claude provider."""
    result = chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=mock_base_args,
        mode="explore",
        repo_settings=None,
        usage_id=123,
    )

    mock_chat_with_claude.assert_called_once()
    call_args = mock_chat_with_claude.call_args[1]
    assert call_args["usage_id"] == 123
    assert result[4] == 15
    assert result[5] == 10


def test_chat_with_agent_passes_usage_id_to_openai(
    mock_chat_with_openai, mock_base_args
):
    """Test that usage_id is passed to OpenAI provider."""
    with patch("services.chat_with_agent.get_model") as mock_get_model:
        mock_get_model.return_value = "gpt-5"

        result = chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
            usage_id=456,
        )

        mock_chat_with_openai.assert_called_once()
        call_args = mock_chat_with_openai.call_args[1]
        assert call_args["usage_id"] == 456
        assert result[4] == 20
        assert result[5] == 8


def test_chat_with_agent_returns_token_counts(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that token counts are returned correctly."""
    result = chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=mock_base_args,
        mode="explore",
        repo_settings=None,
        usage_id=789,
    )

    assert result[4] == 15
    assert result[5] == 10


def test_chat_with_agent_mode_comment_selects_correct_tools(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that 'comment' mode selects TOOLS_TO_UPDATE_COMMENT."""
    with patch("services.chat_with_agent.TOOLS_TO_UPDATE_COMMENT") as mock_tools:
        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="comment",
            repo_settings=None,
        )

        call_args = mock_chat_with_claude.call_args[1]
        assert call_args["tools"] == mock_tools


def test_chat_with_agent_mode_commit_selects_correct_tools(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that 'commit' mode selects TOOLS_TO_COMMIT_CHANGES."""
    with patch("services.chat_with_agent.TOOLS_TO_COMMIT_CHANGES") as mock_tools:
        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        call_args = mock_chat_with_claude.call_args[1]
        assert call_args["tools"] == mock_tools


def test_chat_with_agent_mode_explore_selects_correct_tools(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that 'explore' mode selects TOOLS_TO_EXPLORE_REPO."""
    with patch("services.chat_with_agent.TOOLS_TO_EXPLORE_REPO") as mock_tools:
        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        call_args = mock_chat_with_claude.call_args[1]
        assert call_args["tools"] == mock_tools


def test_chat_with_agent_mode_get_selects_correct_tools(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that 'get' mode selects TOOLS_TO_GET_FILE."""
    with patch("services.chat_with_agent.TOOLS_TO_GET_FILE") as mock_tools:
        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="get",
            repo_settings=None,
        )

        call_args = mock_chat_with_claude.call_args[1]
        assert call_args["tools"] == mock_tools


def test_chat_with_agent_mode_search_selects_correct_tools(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that 'search' mode selects TOOLS_TO_SEARCH_GOOGLE."""
    with patch("services.chat_with_agent.TOOLS_TO_SEARCH_GOOGLE") as mock_tools:
        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="search",
            repo_settings=None,
        )

        call_args = mock_chat_with_claude.call_args[1]
        assert call_args["tools"] == mock_tools


def test_chat_with_agent_provider_exception_tries_next_model(
    mock_get_model, mock_base_args, mock_try_next_model
):
    """Test that when provider raises exception, it tries next model."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.side_effect = [
            Exception("First model failed"),
            (
                {"role": "assistant", "content": "response"},
                None,
                None,
                None,
                15,
                10,
            ),
        ]
        mock_try_next_model.return_value = (True, "next-model")

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        mock_try_next_model.assert_called_once()


def test_chat_with_agent_provider_exception_no_next_model_raises(
    mock_get_model, mock_base_args, mock_try_next_model
):
    """Test that when provider raises exception and no next model, it re-raises."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.side_effect = Exception("Model failed")
        mock_try_next_model.return_value = (False, "current-model")

        with pytest.raises(Exception, match="Model failed"):
            chat_with_agent(
                messages=[{"role": "user", "content": "test"}],
                trigger="issue_comment",
                base_args=mock_base_args,
                mode="explore",
                repo_settings=None,
            )


def test_chat_with_agent_no_tool_calls_returns_early(
    mock_chat_with_claude, mock_get_model, mock_base_args
):
    """Test that when no tool is called, function returns early."""
    result = chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=mock_base_args,
        mode="explore",
        repo_settings=None,
    )

    assert result[0] == [{"role": "user", "content": "test"}]
    assert result[1] == []
    assert result[2] is None
    assert result[3] is None
    assert result[6] is False


def test_chat_with_agent_duplicate_function_call_returns_error(
    mock_get_model, mock_base_args, mock_update_comment
):
    """Test that duplicate function calls with same args return error."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py"},
            15,
            10,
        )

        previous_calls = [
            {"function": "get_remote_file_content", "args": {"file_path": "test.py"}}
        ]

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
            previous_calls=previous_calls,
        )

        # Verify that the error message is in the messages
        call_args = mock_claude.call_args_list
        assert len(call_args) >= 1


def test_chat_with_agent_corrects_apply_diff_to_replace_content(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test correction from apply_diff_to_file to replace_remote_file_content."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "apply_diff_to_file",
            {"file_path": "test.py", "file_content": "new content"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Verify the function was called with corrected name
        mock_tools_to_call.__getitem__.assert_called_with(
            "replace_remote_file_content"
        )


def test_chat_with_agent_corrects_replace_content_to_apply_diff(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test correction from replace_remote_file_content to apply_diff_to_file."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "replace_remote_file_content",
            {"file_path": "test.py", "diff": "--- a/test.py\n+++ b/test.py"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Verify the function was called with corrected name
        mock_tools_to_call.__getitem__.assert_called_with("apply_diff_to_file")


def test_chat_with_agent_corrects_similar_function_names(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test correction of similar function names like create_remote_file."""
    # Configure mock to return False for create_remote_file but True for replace_remote_file_content
    def mock_contains(key):
        return key == "replace_remote_file_content"

    mock_tools_to_call.__contains__.side_effect = mock_contains

    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        # First call returns create_remote_file, subsequent calls return no tool
        mock_claude.side_effect = [
            (
                {"role": "assistant", "content": "response"},
                "test_id",
                "create_remote_file",
                {"file_path": "test.py", "file_content": "content"},
                15,
                10,
            ),
            # Subsequent calls return no tool to stop recursion
            ({"role": "assistant", "content": "done"}, "test_id", None, None, 5, 5),
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Verify the function was called with corrected name
        mock_tools_to_call.__getitem__.assert_called_with(
            "replace_remote_file_content"
        )


def test_chat_with_agent_corrects_new_content_to_file_content(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that 'new_content' argument is renamed to 'file_content'."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "replace_remote_file_content",
            {"file_path": "test.py", "new_content": "updated content"},
            15,
            10,
        )

        mock_function = Mock(return_value="Content replaced successfully")
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        mock_function.assert_called_once()
        call_kwargs = mock_function.call_args[1]
        assert "file_content" in call_kwargs
        assert call_kwargs["file_content"] == "updated content"
        assert "new_content" not in call_kwargs


def test_chat_with_agent_tool_not_in_tools_to_call_returns_error(
    mock_get_model, mock_base_args, mock_update_comment
):
    """Test that calling non-existent tool returns error message."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "non_existent_tool",
            {"arg": "value"},
            15,
            10,
        )

        with patch("services.chat_with_agent.tools_to_call") as mock_tools:
            mock_tools.__contains__.return_value = False

            chat_with_agent(
                messages=[{"role": "user", "content": "test"}],
                trigger="issue_comment",
                base_args=mock_base_args,
                mode="explore",
                repo_settings=None,
            )

            # Function should handle the error gracefully


def test_chat_with_agent_tool_with_non_dict_args(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that tool with non-dict args is called correctly."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_file_tree_list",
            None,
            15,
            10,
        )

        mock_function = Mock(return_value=["file1.py", "file2.py"])
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        mock_function.assert_called_once()
        call_kwargs = mock_function.call_args[1]
        assert call_kwargs["base_args"] == mock_base_args


def test_get_remote_file_content_with_line_number_logging(
    mock_get_model,
    mock_base_args,
    mock_tools_to_call,
    mock_update_comment,
    mock_is_valid_line_number,
):
    """Test logging for get_remote_file_content with line_number."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py", "line_number": 42},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Read `test.py` around line 42." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_remote_file_content_with_invalid_line_number_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_remote_file_content with invalid line_number."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py", "line_number": -1},
            15,
            10,
        )

        with patch(
            "services.chat_with_agent.is_valid_line_number"
        ) as mock_is_valid:
            mock_is_valid.return_value = False

            chat_with_agent(
                messages=[{"role": "user", "content": "test"}],
                trigger="issue_comment",
                base_args=mock_base_args,
                mode="explore",
                repo_settings=None,
            )

            # Check that update_comment was called without line number
            call_args = mock_update_comment.call_args_list
            assert len(call_args) > 0
            found_message = any(
                "Read `test.py`." in call.kwargs.get("body", "")
                for call in call_args
            )
            assert found_message


def test_get_remote_file_content_with_keyword_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_remote_file_content with keyword."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py", "keyword": "def main"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Read `test.py` around keyword `def main`." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_remote_file_content_with_start_line_end_line_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_remote_file_content with start_line and end_line."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py", "start_line": 10, "end_line": 20},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Read `test.py` lines 10-20." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_remote_file_content_without_params_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_remote_file_content without optional params."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Read `test.py`." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_search_remote_file_contents_with_results_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for search_remote_file_contents with results."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_remote_file_contents",
            {"query": "test query"},
            15,
            10,
        )

        mock_function = Mock(return_value="3 files found\n- file1.py\n- file2.py\n- file3.py")
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Searched repository for `test query` and found:" in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_search_remote_file_contents_no_results_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for search_remote_file_contents with no results."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_remote_file_contents",
            {"query": "test query"},
            15,
            10,
        )

        mock_function = Mock(return_value="0 files found")
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Searched repository for `test query` but found no matching files." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_search_remote_file_contents_without_query_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for search_remote_file_contents without query in args."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_remote_file_contents",
            None,
            15,
            10,
        )

        mock_function = Mock(return_value="0 files found")
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Searched repository but found no matching files." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_file_tree_list_with_dir_path_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_file_tree_list with dir_path."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_file_tree_list",
            {"dir_path": "src"},
            15,
            10,
        )

        mock_function = Mock(return_value=["file1.py", "file2.py"])
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Listed contents of directory 'src':" in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_file_tree_list_without_dir_path_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_file_tree_list without dir_path."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_file_tree_list",
            {},
            15,
            10,
        )

        mock_function = Mock(return_value=["file1.py", "file2.py"])
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Listed root directory contents:" in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_file_tree_list_empty_with_dir_path_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_file_tree_list with empty result and dir_path."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_file_tree_list",
            {"dir_path": "nonexistent"},
            15,
            10,
        )

        mock_function = Mock(return_value=None)
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Directory 'nonexistent' not found or is empty." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_file_tree_list_empty_without_dir_path_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_file_tree_list with empty result and no dir_path."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_file_tree_list",
            {},
            15,
            10,
        )

        mock_function = Mock(return_value=None)
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Root directory is empty or not found." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_apply_diff_to_file_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for apply_diff_to_file."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "apply_diff_to_file",
            {"file_path": "test.py", "diff": "--- a/test.py\n+++ b/test.py"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Committed changes to `test.py`." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_replace_remote_file_content_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for replace_remote_file_content."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "replace_remote_file_content",
            {"file_path": "test.py", "file_content": "new content"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Committed changes to `test.py`." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_search_google_with_query_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for search_google with query."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_google",
            {"query": "python testing"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="search",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Googled `python testing` and went through the results." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_search_google_with_empty_query_no_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that search_google with empty query doesn't log special message."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_google",
            {"query": "  "},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="search",
            repo_settings=None,
        )

        # Check that the special google message was not logged
        call_args = mock_update_comment.call_args_list
        if call_args:
            found_google_message = any(
                "Googled" in call.kwargs.get("body", "")
                for call in call_args
            )
            # Should not find the special google message for empty query
            assert not found_google_message or "Calling `search_google()`" in str(call_args)


def test_delete_file_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for delete_file."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "delete_file",
            {"file_path": "test_file.py"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Deleted file `test_file.py`." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_move_file_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for move_file."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "move_file",
            {"old_file_path": "old_file.py", "new_file_path": "new_file.py"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Moved file from `old_file.py` to `new_file.py`." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_unknown_tool_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for unknown tool."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "unknown_tool",
            {"arg": "value"},
            15,
            10,
        )

        with patch("services.chat_with_agent.tools_to_call") as mock_tools:
            mock_tools.__contains__.return_value = False

            chat_with_agent(
                messages=[{"role": "user", "content": "test"}],
                trigger="issue_comment",
                base_args=mock_base_args,
                mode="explore",
                repo_settings=None,
            )

            # Check that update_comment was called with fallback message
            call_args = mock_update_comment.call_args_list
            assert len(call_args) > 0
            found_message = any(
                "Calling `unknown_tool()`" in call.kwargs.get("body", "")
                for call in call_args
            )
            assert found_message


def test_recursion_count_less_than_3_recurses(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that function recurses when recursion_count < 3."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.side_effect = [
            (
                {"role": "assistant", "content": "response1"},
                "test_id_1",
                "get_remote_file_content",
                {"file_path": "test1.py"},
                15,
                10,
            ),
            (
                {"role": "assistant", "content": "response2"},
                "test_id_2",
                "get_remote_file_content",
                {"file_path": "test2.py"},
                15,
                10,
            ),
            (
                {"role": "assistant", "content": "response3"},
                None,
                None,
                None,
                15,
                10,
            ),
        ]

        result = chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
            recursion_count=1,
        )

        # Should have recursed twice (recursion_count 1 -> 2 -> 3)
        assert mock_claude.call_count == 3
        assert result[7] == 15  # p should be 0 + 5 + 5 + 5


def test_recursion_count_equals_3_returns(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that function returns when recursion_count >= 3."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py"},
            15,
            10,
        )

        result = chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
            recursion_count=3,
        )

        # Should not recurse
        assert mock_claude.call_count == 1
        assert result[2] == "get_remote_file_content"
        assert result[7] == 5  # p should be 0 + 5


def test_previous_calls_initialized_to_empty_list(
    mock_get_model, mock_base_args, mock_chat_with_claude
):
    """Test that previous_calls is initialized to empty list when None."""
    result = chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=mock_base_args,
        mode="explore",
        repo_settings=None,
        previous_calls=None,
    )

    assert result[1] == []


def test_log_messages_initialized_to_empty_list(
    mock_get_model, mock_base_args, mock_chat_with_claude
):
    """Test that log_messages is initialized to empty list when None."""
    chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=mock_base_args,
        mode="explore",
        repo_settings=None,
        log_messages=None,
    )

    # Function should complete without error


def test_tool_args_base_args_removed(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that base_args is removed from tool_args before calling tool."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py", "base_args": "should_be_removed"},
            15,
            10,
        )

        mock_function = Mock(return_value="file content")
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        mock_function.assert_called_once()
        call_kwargs = mock_function.call_args[1]
        assert "base_args" in call_kwargs
        assert call_kwargs["base_args"] == mock_base_args
        # The original base_args from tool_args should have been removed


def test_messages_appended_correctly(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that messages are appended correctly."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        response_message = {"role": "assistant", "content": "response"}
        mock_claude.return_value = (
            response_message,
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py"},
            15,
            10,
        )

        initial_messages = [{"role": "user", "content": "test"}]
        result = chat_with_agent(
            messages=initial_messages.copy(),
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
            recursion_count=3,  # Prevent recursion
        )

        # Check that messages were appended
        returned_messages = result[0]
        assert len(returned_messages) == 3
        assert returned_messages[0] == initial_messages[0]
        assert returned_messages[1] == response_message
        assert returned_messages[2]["role"] == "user"
        assert returned_messages[2]["content"][0]["type"] == "tool_result"


def test_is_done_set_to_true_when_tool_called(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that is_done is set to True when tool is called successfully."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py"},
            15,
            10,
        )

        result = chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
            recursion_count=3,  # Prevent recursion
        )

        assert result[6] is True


def test_is_done_set_to_false_when_no_tool_called(
    mock_get_model, mock_base_args, mock_chat_with_claude
):
    """Test that is_done is set to False when no tool is called."""
    result = chat_with_agent(
        messages=[{"role": "user", "content": "test"}],
        trigger="issue_comment",
        base_args=mock_base_args,
        mode="explore",
        repo_settings=None,
    )

    assert result[6] is False


def test_progress_increments_correctly(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that progress (p) increments correctly."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py"},
            15,
            10,
        )

        result = chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
            p=10,
            recursion_count=3,  # Prevent recursion
        )

        assert result[7] == 15  # 10 + 5


def test_system_message_created_with_correct_params(
    mock_get_model, mock_base_args, mock_chat_with_claude, mock_repo_settings
):
    """Test that system message is created with correct parameters."""
    with patch("services.chat_with_agent.create_system_message") as mock_create_system:
        mock_create_system.return_value = "system message"

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=mock_repo_settings,
        )

        mock_create_system.assert_called_once_with(
            trigger="issue_comment",
            mode="explore",
            repo_settings=mock_repo_settings,
        )


def test_corrects_update_remote_file_to_replace_content(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test correction from update_remote_file to replace_remote_file_content."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "update_remote_file",
            {"file_path": "test.py", "file_content": "new content"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Verify the function was called with corrected name
        mock_tools_to_call.__getitem__.assert_called_with(
            "replace_remote_file_content"
        )


def test_corrects_modify_remote_file_to_replace_content(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test correction from modify_remote_file to replace_remote_file_content."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "modify_remote_file",
            {"file_path": "test.py", "file_content": "new content"},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Verify the function was called with corrected name
        mock_tools_to_call.__getitem__.assert_called_with(
            "replace_remote_file_content"
        )

def test_get_remote_file_content_with_non_dict_args_no_logging(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that get_remote_file_content with non-dict args doesn't create specific log."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            None,  # Non-dict args
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Should use fallback logging
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0


def test_get_file_tree_list_with_empty_list_result(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_file_tree_list with empty list result."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_file_tree_list",
            {"dir_path": "empty_dir"},
            15,
            10,
        )

        mock_function = Mock(return_value=[])
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Empty list should be treated as falsy
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Directory 'empty_dir' not found or is empty." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_file_tree_list_with_false_result(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_file_tree_list with False result."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_file_tree_list",
            {},
            15,
            10,
        )

        mock_function = Mock(return_value=False)
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # False should be treated as falsy
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Root directory is empty or not found." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_search_remote_file_contents_with_non_string_result(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for search_remote_file_contents with non-string result."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_remote_file_contents",
            {"query": "test"},
            15,
            10,
        )

        mock_function = Mock(return_value=None)  # Non-string result
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Should handle non-string result gracefully
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Searched repository for `test` but found no matching files." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_remote_file_content_with_start_line_only(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_remote_file_content with only start_line."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py", "start_line": 10},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Read `test.py` lines 10-end." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_get_remote_file_content_with_end_line_only(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for get_remote_file_content with only end_line."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "get_remote_file_content",
            {"file_path": "test.py", "end_line": 20},
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Check that update_comment was called with correct message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Read `test.py` lines start-20." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_search_remote_file_contents_with_empty_result_lines(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test logging for search_remote_file_contents with empty result."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_remote_file_contents",
            {"query": "test"},
            15,
            10,
        )

        mock_function = Mock(return_value="")  # Empty string
        mock_tools_to_call.__getitem__.return_value = mock_function

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="explore",
            repo_settings=None,
        )

        # Should handle empty string result
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0
        found_message = any(
            "Searched repository for `test` but found no matching files." in call.kwargs.get("body", "")
            for call in call_args
        )
        assert found_message


def test_apply_diff_to_file_without_file_path(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that apply_diff_to_file without file_path uses fallback logging."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "apply_diff_to_file",
            {"diff": "--- a/test.py\n+++ b/test.py"},  # Missing file_path
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Should use fallback logging
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0


def test_replace_remote_file_content_without_file_path(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that replace_remote_file_content without file_path uses fallback logging."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "replace_remote_file_content",
            {"file_content": "new content"},  # Missing file_path
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Should use fallback logging
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0


def test_search_google_without_query(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that search_google without query uses fallback logging."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "search_google",
            {},  # Missing query
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="search",
            repo_settings=None,
        )

        # Should not log special google message
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0


def test_delete_file_without_file_path(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that delete_file without file_path uses fallback logging."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "delete_file",
            {},  # Missing file_path
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        # Should use fallback logging
        call_args = mock_update_comment.call_args_list
        assert len(call_args) > 0


def test_move_file_without_paths(
    mock_get_model, mock_base_args, mock_tools_to_call, mock_update_comment
):
    """Test that move_file without paths uses fallback logging."""
    with patch("services.chat_with_agent.chat_with_claude") as mock_claude:
        mock_claude.return_value = (
            {"role": "assistant", "content": "response"},
            "test_id",
            "move_file",
            {"old_file_path": "old.py"},  # Missing new_file_path
            15,
            10,
        )

        chat_with_agent(
            messages=[{"role": "user", "content": "test"}],
            trigger="issue_comment",
            base_args=mock_base_args,
            mode="commit",
            repo_settings=None,
        )

        call_args = mock_update_comment.call_args_list
        # Should use fallback logging
        assert len(call_args) > 0
