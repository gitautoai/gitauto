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
