from services.messages.truncate_text_to_token_limit import (
    truncate_text_to_token_limit,
)


def test_returns_text_unchanged_when_under_limit():
    """No-op path: payload already fits, return as-is."""
    text = "short body"
    assert (
        truncate_text_to_token_limit(text, current_tokens=100, max_tokens=200) == text
    )


def test_returns_text_unchanged_at_exact_limit():
    """Boundary: equal tokens means no truncation."""
    text = "exact"
    assert (
        truncate_text_to_token_limit(text, current_tokens=200, max_tokens=200) == text
    )


def test_truncates_proportionally_with_safety_margin():
    """Reproduces the AGENT-36A/36B/36C path on the helper level: 100k chars, 2M
    tokens, 1M max. keep_ratio = 0.5, with 0.9 safety margin → keep 45000 chars
    plus the truncation marker."""
    text = "x" * 100_000
    result = truncate_text_to_token_limit(
        text, current_tokens=2_000_000, max_tokens=1_000_000
    )
    expected_body = "x" * 45_000
    expected_marker = "\n\n... [truncated at ~1000000 tokens; original was 2000000]"
    assert result == expected_body + expected_marker


def test_truncation_marker_records_original_and_target():
    """Marker must include both the budget (max_tokens) and the original token count (current_tokens) so the caller (and the LLM) can see how aggressive the cut was. Asserting the full result string locks in the marker shape too."""
    text = "abcdefghij" * 1000
    result = truncate_text_to_token_limit(text, current_tokens=500, max_tokens=100)
    # keep_ratio = 100/500 = 0.2; new_len = int(10000 * 0.2 * 0.9) = 1800.
    expected_body = ("abcdefghij" * 1000)[:1800]
    expected_marker = "\n\n... [truncated at ~100 tokens; original was 500]"
    assert result == expected_body + expected_marker


def test_safety_margin_makes_result_strictly_smaller_than_proportional():
    """The 0.9 safety margin is intentional: tokenizer-vs-character ratio isn't
    1:1, so cutting at exactly the proportional length can still go over budget.
    Verify the cut is 90% of the proportional length, not 100%."""
    text = "x" * 1000
    result = truncate_text_to_token_limit(text, current_tokens=1000, max_tokens=500)
    # Proportional cut would be 500 chars; with 0.9 margin we keep 450.
    assert result.startswith("x" * 450)
    assert not result.startswith("x" * 451)
