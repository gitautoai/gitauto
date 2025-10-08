# pylint: disable=redefined-outer-name
from unittest.mock import Mock, patch

import pytest
from services.chat_with_agent import chat_with_agent


@pytest.fixture
def mock_base_args():
    """Fixture to create a mock BaseArgs object."""
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
def mock_update_comment():
    """Fixture to mock update_comment function."""
    with patch("services.chat_with_agent.update_comment") as mock:
        yield mock


@pytest.fixture
def mock_create_system_message():
    """Fixture to mock create_system_message function."""
    with patch("services.chat_with_agent.create_system_message") as mock:
        mock.return_value = "system message"
        yield mock


def test_chat_with_agent_passes_usage_id_to_claude(
    mock_chat_with_claude, mock_get_model, mock_base_args, mock_create_system_message
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


def test_chat_with_agent_returns_token_counts(
    mock_chat_with_claude, mock_get_model, mock_base_args, mock_create_system_message
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


def test_chat_with_agent_no_tool_calls_returns_early(
    mock_chat_with_claude, mock_get_model, mock_base_args, mock_create_system_message
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


def test_chat_with_agent_mode_comment_selects_correct_tools(
    mock_chat_with_claude, mock_get_model, mock_base_args, mock_create_system_message
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
    mock_chat_with_claude, mock_get_model, mock_base_args, mock_create_system_message
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
    mock_chat_with_claude, mock_get_model, mock_base_args, mock_create_system_message
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


def test_chat_with_agent_previous_calls_initialized_to_empty_list(
    mock_get_model, mock_base_args, mock_chat_with_claude, mock_create_system_message
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


def test_chat_with_agent_is_done_set_to_false_when_no_tool_called(
    mock_get_model, mock_base_args, mock_chat_with_claude, mock_create_system_message
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


def test_chat_with_agent_system_message_created_with_correct_params(
    mock_get_model, mock_base_args, mock_chat_with_claude
):
    """Test that system message is created with correct parameters."""
    with patch("services.chat_with_agent.create_system_message") as mock_create_system:
        mock_create_system.return_value = "system message"
        mock_repo_settings = Mock()

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
