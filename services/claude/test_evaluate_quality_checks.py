# pyright: reportArgumentType=false
from unittest.mock import MagicMock, patch

from constants.claude import MAX_OUTPUT_TOKENS
from constants.models import ClaudeModelId
from services.claude.evaluate_quality_checks import evaluate_quality_checks


def _mock_claude_call(mock_claude, model: ClaudeModelId):
    mock_content = MagicMock()
    mock_content.text = '{"business_logic": {}}'
    mock_claude.messages.create.return_value = MagicMock(content=[mock_content])

    evaluate_quality_checks(
        source_content="const x = 1;",
        source_path="src/foo.ts",
        test_files=[("test/foo.spec.ts", "it('works', () => {})")],
        model=model,
    )

    return mock_claude.messages.create.call_args.kwargs


@patch("services.claude.evaluate_quality_checks.claude")
def test_opus_47_passes_model_and_max_tokens(mock_claude):
    kwargs = _mock_claude_call(mock_claude, ClaudeModelId.OPUS_4_7)
    assert kwargs["model"] == "claude-opus-4-7"
    assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS[ClaudeModelId.OPUS_4_7]


@patch("services.claude.evaluate_quality_checks.claude")
def test_opus_46_passes_model_and_max_tokens(mock_claude):
    kwargs = _mock_claude_call(mock_claude, ClaudeModelId.OPUS_4_6)
    assert kwargs["model"] == "claude-opus-4-6"
    assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS[ClaudeModelId.OPUS_4_6]


@patch("services.claude.evaluate_quality_checks.claude")
def test_sonnet_46_passes_model_and_max_tokens(mock_claude):
    kwargs = _mock_claude_call(mock_claude, ClaudeModelId.SONNET_4_6)
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS[ClaudeModelId.SONNET_4_6]


@patch("services.claude.evaluate_quality_checks.claude")
def test_opus_45_passes_model_and_max_tokens(mock_claude):
    kwargs = _mock_claude_call(mock_claude, ClaudeModelId.OPUS_4_5)
    assert kwargs["model"] == "claude-opus-4-5"
    assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS[ClaudeModelId.OPUS_4_5]


@patch("services.claude.evaluate_quality_checks.claude")
def test_sonnet_45_passes_model_and_max_tokens(mock_claude):
    kwargs = _mock_claude_call(mock_claude, ClaudeModelId.SONNET_4_5)
    assert kwargs["model"] == "claude-sonnet-4-5"
    assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS[ClaudeModelId.SONNET_4_5]


@patch("services.claude.evaluate_quality_checks.claude")
def test_haiku_45_passes_model_and_max_tokens(mock_claude):
    kwargs = _mock_claude_call(mock_claude, ClaudeModelId.HAIKU_4_5)
    assert kwargs["model"] == "claude-haiku-4-5"
    assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS[ClaudeModelId.HAIKU_4_5]
