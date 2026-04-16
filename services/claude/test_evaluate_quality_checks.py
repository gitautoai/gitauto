# pyright: reportArgumentType=false
from unittest.mock import MagicMock, patch

from constants.models import ClaudeModelId
from services.claude.evaluate_quality_checks import evaluate_quality_checks


@patch("services.claude.evaluate_quality_checks.claude")
def test_uses_opus_model(mock_claude):
    mock_content = MagicMock()
    mock_content.text = '{"business_logic": {}}'
    mock_claude.messages.create.return_value = MagicMock(content=[mock_content])

    evaluate_quality_checks(
        source_content="const x = 1;",
        source_path="src/foo.ts",
        test_files=[("test/foo.spec.ts", "it('works', () => {})")],
        model=ClaudeModelId.OPUS_4_6,
    )

    call_kwargs = mock_claude.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-6"


@patch("services.claude.evaluate_quality_checks.claude")
def test_uses_max_tokens_matching_model(mock_claude):
    mock_content = MagicMock()
    mock_content.text = '{"business_logic": {}}'
    mock_claude.messages.create.return_value = MagicMock(content=[mock_content])

    evaluate_quality_checks(
        source_content="const x = 1;",
        source_path="src/foo.ts",
        test_files=[("test/foo.spec.ts", "it('works', () => {})")],
        model=ClaudeModelId.OPUS_4_6,
    )

    call_kwargs = mock_claude.messages.create.call_args.kwargs
    # Opus 4.6 has 128_000 max tokens
    assert call_kwargs["max_tokens"] == 128_000
