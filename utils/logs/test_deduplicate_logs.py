from config import UTF8
from utils.logs.deduplicate_repetitive_logs import deduplicate_repetitive_logs


def test_deduplicate_repetitive_logs_with_real_sample():
    with open(
        "services/github/workflow_runs/get_workflow_run_logs_duplicated.txt",
        "r",
        encoding=UTF8,
    ) as f:
        original_log = f.read()

    with open(
        "services/github/workflow_runs/get_workflow_run_logs_deduplicated.txt",
        "r",
        encoding=UTF8,
    ) as f:
        expected_content = f.read()

    deduplicated = deduplicate_repetitive_logs(original_log)

    original_lines = original_log.split("\n")
    deduplicated_lines = deduplicated.split("\n")
    expected_lines = expected_content.split("\n")

    # Check exact line count matches expected
    assert (
        len(original_lines) == 14581
    ), f"Expected 14581 original lines, got {len(original_lines)}"
    assert (
        len(deduplicated_lines) == 280
    ), f"Expected 280 deduplicated lines, got {len(deduplicated_lines)}"
    assert (
        len(expected_lines) == 280
    ), f"Expected file should have 280 lines, got {len(expected_lines)}"

    # Check content matches exactly
    assert (
        deduplicated == expected_content
    ), "Deduplicated content should match expected file exactly"
