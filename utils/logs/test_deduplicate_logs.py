import pytest
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


def test_no_repetitive_logs():
    """Test that non-repetitive logs remain unchanged."""
    log_content = "Line 1\nLine 2\nLine 3\nLine 4"
    result = deduplicate_repetitive_logs(log_content)
    assert result == log_content


def test_empty_log():
    """Test that empty log content returns empty string."""
    result = deduplicate_repetitive_logs("")
    assert result == ""


def test_single_line_log():
    """Test that single line log remains unchanged."""
    log_content = "Single line"
    result = deduplicate_repetitive_logs(log_content)
    assert result == log_content


def test_two_line_repetition():
    """Test that two identical lines don't get deduplicated (need 3+ occurrences)."""
    log_content = "Line 1\nLine 1\nLine 2"
    result = deduplicate_repetitive_logs(log_content)
    assert result == log_content


def test_three_consecutive_identical_lines():
    """Test that three consecutive identical lines get deduplicated to one."""
    log_content = "Line 1\nLine 1\nLine 1\nLine 2"
    expected = "Line 1\nLine 2"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_four_consecutive_identical_lines():
    """Test that four consecutive identical lines get deduplicated to one."""
    log_content = "Line 1\nLine 1\nLine 1\nLine 1\nLine 2"
    expected = "Line 1\nLine 2"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_multiple_repetitive_blocks():
    """Test multiple separate blocks of repetitive lines."""
    log_content = "Start\nError A\nError A\nError A\nMiddle\nError B\nError B\nError B\nEnd"
    expected = "Start\nError A\nMiddle\nError B\nEnd"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_non_consecutive_repetitions():
    """Test that non-consecutive repetitions are not deduplicated."""
    log_content = "Line 1\nLine 2\nLine 1\nLine 3\nLine 1"
    result = deduplicate_repetitive_logs(log_content)
    assert result == log_content


def test_pattern_of_two_lines():
    """Test deduplication of repetitive two-line patterns."""
    log_content = "Error: Connection failed\nRetrying...\nError: Connection failed\nRetrying...\nError: Connection failed\nRetrying...\nSuccess"
    expected = "Error: Connection failed\nRetrying...\nSuccess"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_pattern_of_three_lines():
    """Test deduplication of repetitive three-line patterns."""
    log_content = "Step 1\nStep 2\nStep 3\nStep 1\nStep 2\nStep 3\nStep 1\nStep 2\nStep 3\nDone"
    expected = "Step 1\nStep 2\nStep 3\nDone"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_mixed_patterns():
    """Test logs with both single line and multi-line repetitive patterns."""
    log_content = "Start\nError A\nError A\nError A\nStep 1\nStep 2\nStep 1\nStep 2\nStep 1\nStep 2\nEnd"
    expected = "Start\nError A\nStep 1\nStep 2\nEnd"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_overlapping_patterns():
    """Test handling of overlapping patterns."""
    log_content = "A\nB\nA\nB\nA\nB\nA\nC"
    # The pattern "A\nB" repeats 3 times consecutively
    expected = "A\nB\nA\nC"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_large_pattern():
    """Test deduplication of larger patterns."""
    pattern = "\n".join([f"Line {i}" for i in range(1, 6)])  # 5-line pattern
    log_content = f"{pattern}\n{pattern}\n{pattern}\nFinal line"
    expected = f"{pattern}\nFinal line"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_pattern_at_end():
    """Test repetitive pattern at the end of logs."""
    log_content = "Start\nError\nError\nError"
    expected = "Start\nError"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_pattern_at_beginning():
    """Test repetitive pattern at the beginning of logs."""
    log_content = "Error\nError\nError\nEnd"
    expected = "Error\nEnd"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_whitespace_lines():
    """Test handling of whitespace and empty lines."""
    log_content = "Line 1\n\n\n\nLine 2"
    expected = "Line 1\n\nLine 2"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_identical_but_spaced_patterns():
    """Test that identical patterns separated by other content are not deduplicated."""
    log_content = "Error A\nError A\nError A\nOther line\nError A\nError A\nError A"
    expected = "Error A\nOther line\nError A"
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected


def test_complex_real_world_scenario():
    """Test a complex real-world-like scenario with multiple types of repetitions."""
    log_content = """Starting process
Connecting to database
Connection failed
Retrying connection
Connection failed
Retrying connection
Connection failed
Retrying connection
Connected successfully
Processing item 1
Processing item 2
Error in processing
Error in processing
Error in processing"""
    
    expected = """Starting process
Connecting to database
Connection failed
Retrying connection
Connected successfully
Processing item 1
Processing item 2
Error in processing"""
    
    result = deduplicate_repetitive_logs(log_content)
    assert result == expected