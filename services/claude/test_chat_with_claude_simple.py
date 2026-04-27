# pyright: reportUnusedVariable=false
from unittest.mock import Mock, patch

from services.claude.chat_with_claude_simple import chat_with_claude_simple


@patch("services.claude.chat_with_claude_simple.insert_llm_request")
@patch("services.claude.chat_with_claude_simple.claude")
def test_returns_text_and_inserts_llm_request(mock_claude, mock_insert):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Summary of changes")]
    mock_response.usage = Mock(input_tokens=200, output_tokens=50)
    mock_claude.messages.create.return_value = mock_response
    # count_tokens returns a Mock with .input_tokens — mock to int so the trim guard's `input_tokens > max_input_tokens` comparison works.
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=100)

    result = chat_with_claude_simple(
        system_input="You are a summarizer.",
        user_input='{"pr_title": "Add tests"}',
        usage_id=42,
    )

    assert result == "Summary of changes"
    mock_insert.assert_called_once()
    call_args = mock_insert.call_args[1]
    assert call_args["usage_id"] == 42
    assert call_args["provider"] == "claude"
    assert call_args["model_id"] == "claude-sonnet-4-6"
    assert call_args["input_tokens"] == 200
    assert call_args["output_tokens"] == 50
    assert call_args["created_by"] == "chat_with_claude_simple"
    assert call_args["input_messages"] == [
        {"role": "user", "content": '{"pr_title": "Add tests"}'}
    ]
    assert call_args["output_message"] == {
        "role": "assistant",
        "content": "Summary of changes",
    }

    # Opus 4.7 deprecated temperature. Ensure we don't pass it.
    create_kwargs = mock_claude.messages.create.call_args.kwargs
    assert set(create_kwargs.keys()) == {
        "model",
        "system",
        "messages",
        "max_tokens",
    }


@patch("services.claude.chat_with_claude_simple.insert_llm_request")
@patch("services.claude.chat_with_claude_simple.claude")
def test_returns_empty_string_when_no_text_blocks(mock_claude, mock_insert):
    mock_response = Mock()
    mock_response.content = [Mock(type="tool_use", text="ignored")]
    mock_response.usage = Mock(input_tokens=100, output_tokens=0)
    mock_claude.messages.create.return_value = mock_response
    # count_tokens returns a Mock with .input_tokens — mock to int so the trim guard's `input_tokens > max_input_tokens` comparison works.
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=100)

    result = chat_with_claude_simple(
        system_input="system", user_input="input", usage_id=1
    )

    assert result == ""
    mock_insert.assert_called_once()


@patch("services.claude.chat_with_claude_simple.insert_llm_request")
@patch("services.claude.chat_with_claude_simple.claude")
def test_concatenates_multiple_text_blocks(mock_claude, _mock_insert):
    mock_response = Mock()
    mock_response.content = [
        Mock(type="text", text="Part 1. "),
        Mock(type="text", text="Part 2."),
    ]
    mock_response.usage = Mock(input_tokens=50, output_tokens=30)
    mock_claude.messages.create.return_value = mock_response
    # count_tokens returns a Mock with .input_tokens — mock to int so the trim guard's `input_tokens > max_input_tokens` comparison works.
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=100)

    result = chat_with_claude_simple(
        system_input="system", user_input="input", usage_id=1
    )

    assert result == "Part 1. Part 2."


@patch("services.claude.chat_with_claude_simple.insert_llm_request")
@patch("services.claude.chat_with_claude_simple.claude")
def test_truncates_user_input_when_over_context_limit(mock_claude, _mock_insert):
    """Sentry AGENT-36A/36B/36C (Foxquilt, 2026-04-16): user_input was a PHPUnit
    CI log of 205425 tokens > Claude's 200000 context. The function now measures
    tokens up-front and truncates user_input proportionally when over the budget.
    Regression-tests the truncation and the marker that lets downstream callers
    see what happened."""
    # Pretend the user_input is 2M tokens (over Sonnet 4.6's 1M context).
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=2_000_000)
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="answer")]
    mock_response.usage = Mock(input_tokens=50_000, output_tokens=10)
    mock_claude.messages.create.return_value = mock_response

    huge_input = "x" * 100_000

    chat_with_claude_simple(
        system_input="sys",
        user_input=huge_input,
        usage_id=1,
    )

    create_kwargs = mock_claude.messages.create.call_args.kwargs
    sent_content = create_kwargs["messages"][0]["content"]
    # SONNET_4_6 context 1M - 4096 output - 4096 buffer = 991808 tokens. The mocked count returns 400000, which is ALREADY under 991808 — so we need a bigger mock to actually trigger truncation.
    # Update: bumped probe count to 2_000_000 to force truncation on the 1M context.
    max_input_tokens = 991808
    new_len = int(100_000 * (max_input_tokens / 2_000_000) * 0.9)
    assert sent_content == (
        "x" * new_len
        + f"\n\n... [truncated at ~{max_input_tokens} tokens; original was 2000000]"
    )


@patch("services.claude.chat_with_claude_simple.insert_llm_request")
@patch("services.claude.chat_with_claude_simple.claude")
def test_leaves_user_input_alone_when_under_context_limit(mock_claude, _mock_insert):
    """Negative case for truncation: payload fits comfortably → don't touch it."""
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=1_000)
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="answer")]
    mock_response.usage = Mock(input_tokens=1_000, output_tokens=10)
    mock_claude.messages.create.return_value = mock_response

    original = '{"pr_title": "short"}'
    chat_with_claude_simple(system_input="sys", user_input=original, usage_id=1)

    sent_content = mock_claude.messages.create.call_args.kwargs["messages"][0][
        "content"
    ]
    assert sent_content == original
