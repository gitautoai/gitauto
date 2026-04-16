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

    assert "adversarial.null_undefined_inputs: No null tests" in result
    assert "security.command_injection: No injection tests" in result
    assert "business_logic" not in result


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

    assert result == ""
