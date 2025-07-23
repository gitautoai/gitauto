import pytest
from utils.time.get_timeout_message import get_timeout_message


def test_get_timeout_message_with_default_process_name():
    """Test that get_timeout_message returns correct message with default process name."""
    elapsed_time = 45.7
    expected = "Process stopped due to Lambda timeout limit (45.7s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_with_custom_process_name():
    """Test that get_timeout_message returns correct message with custom process name."""
    elapsed_time = 120.3
    process_name = "Data Processing"
    expected = "Data Processing stopped due to Lambda timeout limit (120.3s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_zero_elapsed_time():
    """Test that get_timeout_message handles zero elapsed time correctly."""
    elapsed_time = 0.0
    expected = "Process stopped due to Lambda timeout limit (0.0s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_with_small_elapsed_time():
    """Test that get_timeout_message handles small elapsed time correctly."""
    elapsed_time = 0.1
    expected = "Process stopped due to Lambda timeout limit (0.1s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_with_large_elapsed_time():
    """Test that get_timeout_message handles large elapsed time correctly."""
    elapsed_time = 999.9
    expected = "Process stopped due to Lambda timeout limit (999.9s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_with_integer_elapsed_time():
    """Test that get_timeout_message handles integer elapsed time correctly."""
    elapsed_time = 60
    expected = "Process stopped due to Lambda timeout limit (60.0s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_with_empty_process_name():
    """Test that get_timeout_message handles empty process name correctly."""
    elapsed_time = 30.5
    process_name = ""
    expected = " stopped due to Lambda timeout limit (30.5s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_special_characters_in_process_name():
    """Test that get_timeout_message handles special characters in process name."""
    elapsed_time = 75.2
    process_name = "API-Call_Process#1"
    expected = "API-Call_Process#1 stopped due to Lambda timeout limit (75.2s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_unicode_process_name():
    """Test that get_timeout_message handles unicode characters in process name."""
    elapsed_time = 42.8
    process_name = "データ処理"
    expected = "データ処理 stopped due to Lambda timeout limit (42.8s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_long_process_name():
    """Test that get_timeout_message handles long process name correctly."""
    elapsed_time = 88.1
    process_name = "Very Long Process Name That Exceeds Normal Length Expectations"
    expected = "Very Long Process Name That Exceeds Normal Length Expectations stopped due to Lambda timeout limit (88.1s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_decimal_precision():
    """Test that get_timeout_message formats elapsed time to one decimal place."""
    elapsed_time = 123.456789
    expected = "Process stopped due to Lambda timeout limit (123.5s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


@pytest.mark.parametrize(
    "elapsed_time,process_name,expected",
    [
        (
            10.0,
            "Test",
            "Test stopped due to Lambda timeout limit (10.0s elapsed). Proceeding with current progress.",
        ),
        (
            25.7,
            "API Handler",
            "API Handler stopped due to Lambda timeout limit (25.7s elapsed). Proceeding with current progress.",
        ),
        (
            0.5,
            "Quick Task",
            "Quick Task stopped due to Lambda timeout limit (0.5s elapsed). Proceeding with current progress.",
        ),
        (
            300.0,
            "Long Running Process",
            "Long Running Process stopped due to Lambda timeout limit (300.0s elapsed). Proceeding with current progress.",
        ),
    ],
)
def test_get_timeout_message_parametrized(elapsed_time, process_name, expected):
    """Test get_timeout_message with various parameter combinations."""
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_exception_handling():
    """Test that get_timeout_message is decorated with handle_exceptions."""
    # Test that the function is decorated with handle_exceptions
    # This test verifies the decorator is applied correctly
    assert hasattr(get_timeout_message, "__wrapped__")


def test_get_timeout_message_real_world_usage_scenarios():
    """Test get_timeout_message with real-world usage scenarios from the codebase."""
    # Test scenario from pr_checkbox_handler.py
    elapsed_time = 850.5  # Close to Lambda timeout limit
    process_name = "PR test generation processing"
    expected = "PR test generation processing stopped due to Lambda timeout limit (850.5s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_negative_elapsed_time():
    """Test that get_timeout_message handles negative elapsed time correctly."""
    elapsed_time = -5.0
    expected = "Process stopped due to Lambda timeout limit (-5.0s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_with_very_precise_elapsed_time():
    """Test that get_timeout_message rounds elapsed time to one decimal place."""
    elapsed_time = 123.456789123
    expected = "Process stopped due to Lambda timeout limit (123.5s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_with_whitespace_process_name():
    """Test that get_timeout_message handles process name with whitespace."""
    elapsed_time = 45.0
    process_name = "  Process with spaces  "
    expected = "  Process with spaces   stopped due to Lambda timeout limit (45.0s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_newline_in_process_name():
    """Test that get_timeout_message handles process name with newline characters."""
    elapsed_time = 30.0
    process_name = "Process\nwith\nnewlines"
    expected = "Process\nwith\nnewlines stopped due to Lambda timeout limit (30.0s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_tab_in_process_name():
    """Test that get_timeout_message handles process name with tab characters."""
    elapsed_time = 15.5
    process_name = "Process\twith\ttabs"
    expected = "Process\twith\ttabs stopped due to Lambda timeout limit (15.5s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_with_quotes_in_process_name():
    """Test that get_timeout_message handles process name with quotes."""
    elapsed_time = 67.3
    process_name = 'Process "with" quotes'
    expected = 'Process "with" quotes stopped due to Lambda timeout limit (67.3s elapsed). Proceeding with current progress.'
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_edge_case_very_small_time():
    """Test get_timeout_message with very small elapsed time."""
    elapsed_time = 0.01
    expected = "Process stopped due to Lambda timeout limit (0.0s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


def test_get_timeout_message_edge_case_lambda_timeout_limit():
    """Test get_timeout_message with elapsed time at Lambda timeout limit."""
    elapsed_time = 900.0  # AWS Lambda timeout limit
    expected = "Process stopped due to Lambda timeout limit (900.0s elapsed). Proceeding with current progress."
    result = get_timeout_message(elapsed_time)
    assert result == expected


@pytest.mark.parametrize(
    "elapsed_time", [0.0, 0.1, 1.0, 10.5, 60.0, 120.7, 300.0, 600.5, 900.0, 999.9]
)
def test_get_timeout_message_various_elapsed_times(elapsed_time):
    """Test get_timeout_message with various elapsed time values."""
    result = get_timeout_message(elapsed_time)
    expected_time_str = f"{elapsed_time:.1f}s"
    assert expected_time_str in result
    assert "stopped due to Lambda timeout limit" in result
    assert "Proceeding with current progress." in result


@pytest.mark.parametrize(
    "process_name",
    [
        "Process",
        "API Handler",
        "Data Processing",
        "File Upload",
        "Database Query",
        "Email Service",
        "Image Processing",
        "Report Generation",
        "Backup Process",
    ],
)
def test_get_timeout_message_various_process_names(process_name):
    """Test get_timeout_message with various process names."""
    elapsed_time = 45.0
    result = get_timeout_message(elapsed_time, process_name)
    assert result.startswith(process_name)
    assert "stopped due to Lambda timeout limit (45.0s elapsed)" in result
    assert result.endswith("Proceeding with current progress.")
