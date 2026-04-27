# pyright: reportArgumentType=false
from unittest.mock import patch

from services.agents.run_quality_gate import run_quality_gate


@patch("services.agents.run_quality_gate.evaluate_quality_checks")
@patch("services.agents.run_quality_gate.read_local_file")
def test_returns_specific_failure_details(
    mock_read, mock_evaluate, create_test_base_args
):
    mock_read.side_effect = lambda file_path, base_dir: "file content"
    mock_evaluate.return_value = {
        "adversarial": {
            "null_undefined_inputs": {
                "status": "fail",
                "reason": "No null tests",
            }
        },
        "security": {
            "command_injection": {
                "status": "fail",
                "reason": "No injection tests",
            }
        },
        "business_logic": {
            "domain_rules": {"status": "pass", "reason": ""},
        },
    }

    base_args = create_test_base_args(test_file_paths=["test/foo.spec.ts"])
    result = run_quality_gate("/tmp/clone", "src/foo.ts", base_args)

    # Exact result: header + one fail line per category that hit a 'fail' (passes/na are not in error).
    # Iteration order follows dict insertion order (adversarial, security, business_logic).
    assert result.error == (
        "Quality gate failed for src/foo.ts:\n"
        "adversarial.null_undefined_inputs: No null tests\n"
        "security.command_injection: No injection tests"
    )
    # 3 total checks counted, 2 categories with failures → passed_count = 3 - 2 = 1.
    assert result.passed_count == 1


@patch("services.agents.run_quality_gate.evaluate_quality_checks")
@patch("services.agents.run_quality_gate.read_local_file")
def test_returns_empty_when_all_pass(mock_read, mock_evaluate, create_test_base_args):
    mock_read.side_effect = lambda file_path, base_dir: "file content"
    mock_evaluate.return_value = {
        "business_logic": {
            "domain_rules": {"status": "pass", "reason": ""},
        },
        "security": {
            "xss": {"status": "na", "reason": "Not applicable"},
        },
    }

    base_args = create_test_base_args(test_file_paths=["test/foo.spec.ts"])
    result = run_quality_gate("/tmp/clone", "src/foo.ts", base_args)

    assert result.error == ""
    assert result.passed_count == 2


@patch("services.agents.run_quality_gate.evaluate_quality_checks")
@patch("services.agents.run_quality_gate.read_local_file")
def test_breaks_after_first_fail_in_category(
    mock_read, mock_evaluate, create_test_base_args
):
    # Inner loop must short-circuit after the first 'fail' in a category, not record both.
    # If two checks in the same category fail, we still report one failure for that category.
    mock_read.side_effect = lambda file_path, base_dir: "file content"
    mock_evaluate.return_value = {
        "adversarial": {
            "null_undefined_inputs": {"status": "fail", "reason": "first"},
            "boundary_values": {"status": "fail", "reason": "second"},
        },
    }

    base_args = create_test_base_args(test_file_paths=["test/foo.spec.ts"])
    result = run_quality_gate("/tmp/clone", "src/foo.ts", base_args)

    # Only the FIRST fail in the category is recorded; the inner break stops further iteration.
    assert result.error == (
        "Quality gate failed for src/foo.ts:\n"
        "adversarial.null_undefined_inputs: first"
    )
    # The inner break stops counting after the first fail, so total_checks=1.
    # passed_count = total_checks (1) - len(failed_categories) (1) = 0.
    assert result.passed_count == 0
