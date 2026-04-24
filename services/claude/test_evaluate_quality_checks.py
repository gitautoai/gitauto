# pyright: reportArgumentType=false
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from constants.claude import MAX_OUTPUT_TOKENS
from constants.models import ClaudeModelId, GoogleModelId
from services.claude.evaluate_quality_checks import evaluate_quality_checks


@pytest.fixture(autouse=True)
def mock_insert_llm_request():
    with patch("services.claude.evaluate_quality_checks.insert_llm_request") as mock:
        yield mock


def _mock_claude_call(mock_claude, model: ClaudeModelId):
    mock_content = MagicMock()
    mock_content.text = '{"business_logic": {}}'
    mock_claude.messages.create.return_value = MagicMock(content=[mock_content])

    evaluate_quality_checks(
        source_content="const x = 1;",
        source_path="src/foo.ts",
        test_files=[("test/foo.spec.ts", "it('works', () => {})")],
        model=model,
        usage_id=1,
        created_by="tester",
    )

    return mock_claude.messages.create.call_args.kwargs


@patch("services.claude.evaluate_quality_checks.claude")
def test_opus_47_passes_model_and_max_tokens(mock_claude):
    kwargs = _mock_claude_call(mock_claude, ClaudeModelId.OPUS_4_7)
    assert kwargs["model"] == "claude-opus-4-7"
    assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS[ClaudeModelId.OPUS_4_7]
    # Opus 4.7 deprecated temperature; ensure we don't pass it for any Claude model.
    assert set(kwargs.keys()) == {"model", "max_tokens", "system", "messages"}


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


@pytest.mark.integration
def test_gemma_returns_case_coverage_for_real_file_pair():
    """Real Gemma call: verify case_coverage category is graded for a real source+test pair."""
    repo_root = Path(__file__).resolve().parents[2]
    src_path = "services/claude/forget_messages.py"
    test_path = "services/claude/test_forget_messages.py"
    src_content = (repo_root / src_path).read_text()
    test_content = (repo_root / test_path).read_text()

    result = evaluate_quality_checks(
        source_content=src_content,
        source_path=src_path,
        test_files=[(test_path, test_content)],
        model=GoogleModelId.GEMMA_4_31B,
        usage_id=None,
        created_by="integration-test",
    )

    assert result is not None
    # Access directly — KeyError if missing
    case_cov = result["case_coverage"]
    assert set(case_cov.keys()) == {
        "dimension_enumeration",
        "combinatorial_matrix",
        "explicit_expected_per_cell",
    }
    for check_name, check_data in case_cov.items():
        assert check_data["status"] in {
            "pass",
            "fail",
            "na",
        }, f"{check_name} has invalid status {check_data.get('status')!r}"


# Shared source: a small pure function with 3 independent input dimensions
# (sign of amount, currency, customer_tier) -> 2*3*3 = 18 business cases.
_DISCOUNT_SRC = '''
def apply_discount(amount: float, currency: str, customer_tier: str) -> float:
    """Return discounted amount. Premium gets 20%, gold 10%, standard 0%.
    Non-USD gets extra 5% off. Negative amounts return 0."""
    if amount < 0:
        return 0.0
    discount = 0.0
    if customer_tier == "premium":
        discount = 0.20
    elif customer_tier == "gold":
        discount = 0.10
    if currency != "USD":
        discount += 0.05
    return amount * (1 - discount)
'''

_WEAK_TEST = """
from src.discount import apply_discount

def test_premium_usd():
    assert apply_discount(100.0, "USD", "premium") == 80.0
"""

_STRONG_TEST = """
import pytest
from src.discount import apply_discount

# Matrix: sign x currency x tier -> expected (derived from business rules, not code)
@pytest.mark.parametrize("amount,currency,tier,expected", [
    # Negative amount early-returns 0 regardless of other dims (pruned)
    (-1.0, "USD", "standard", 0.0),
    # Positive amount, full matrix of currency x tier
    (100.0, "USD", "standard", 100.0),
    (100.0, "USD", "gold", 90.0),
    (100.0, "USD", "premium", 80.0),
    (100.0, "EUR", "standard", 95.0),
    (100.0, "EUR", "gold", 85.0),
    (100.0, "EUR", "premium", 75.0),
    (100.0, "JPY", "standard", 95.0),
    (100.0, "JPY", "gold", 85.0),
    (100.0, "JPY", "premium", 75.0),
])
def test_discount_matrix(amount, currency, tier, expected):
    assert apply_discount(amount, currency, tier) == expected
"""


@pytest.mark.integration
def test_gemma_discriminates_weak_vs_strong_case_coverage():
    """Gemma should grade a 1-case test worse than a full matrix on case_coverage."""
    weak_result = evaluate_quality_checks(
        source_content=_DISCOUNT_SRC,
        source_path="src/discount.py",
        test_files=[("tests/test_discount.py", _WEAK_TEST)],
        model=GoogleModelId.GEMMA_4_31B,
        usage_id=None,
        created_by="integration-test",
    )
    strong_result = evaluate_quality_checks(
        source_content=_DISCOUNT_SRC,
        source_path="src/discount.py",
        test_files=[("tests/test_discount.py", _STRONG_TEST)],
        model=GoogleModelId.GEMMA_4_31B,
        usage_id=None,
        created_by="integration-test",
    )

    assert weak_result is not None and strong_result is not None
    weak_cov = weak_result["case_coverage"]
    strong_cov = strong_result["case_coverage"]

    weak_fails = sum(1 for c in weak_cov.values() if c["status"] == "fail")
    strong_fails = sum(1 for c in strong_cov.values() if c["status"] == "fail")

    print("\nWEAK case_coverage:")
    for name, data in weak_cov.items():
        print(f"  {name}: {data['status']} — {data.get('reason', '')}")
    print("\nSTRONG case_coverage:")
    for name, data in strong_cov.items():
        print(f"  {name}: {data['status']} — {data.get('reason', '')}")

    # The weak test (1 case for 18-cell matrix) must fail more checks than the strong test.
    assert (
        weak_fails > strong_fails
    ), f"Gemma did not discriminate: weak_fails={weak_fails}, strong_fails={strong_fails}"
    # The weak test must fail combinatorial_matrix specifically — it only has 1 case.
    assert weak_cov["combinatorial_matrix"]["status"] == "fail"
