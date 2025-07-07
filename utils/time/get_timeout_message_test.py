from unittest.mock import patch
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


@pytest.mark.parametrize("elapsed_time,process_name,expected", [
    (10.0, "Test", "Test stopped due to Lambda timeout limit (10.0s elapsed). Proceeding with current progress."),
    (25.7, "API Handler", "API Handler stopped due to Lambda timeout limit (25.7s elapsed). Proceeding with current progress."),
    (0.5, "Quick Task", "Quick Task stopped due to Lambda timeout limit (0.5s elapsed). Proceeding with current progress."),
    (300.0, "Long Running Process", "Long Running Process stopped due to Lambda timeout limit (300.0s elapsed). Proceeding with current progress."),
])
def test_get_timeout_message_parametrized(elapsed_time, process_name, expected):
    """Test get_timeout_message with various parameter combinations."""
    result = get_timeout_message(elapsed_time, process_name)
    assert result == expected


def test_get_timeout_message_exception_handling():
    """Test that get_timeout_message returns default value when exception occurs."""
    with patch('utils.time.get_timeout_message.handle_exceptions') as mock_decorator:
        # Configure the mock to simulate the decorator behavior
        def mock_decorator_func(default_return_value="", raise_on_error=False):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    return default_return_value  # Return default value on exception
                return wrapper
            return decorator
        
        mock_decorator.side_effect = mock_decorator_func
        
        # Import the function again to get the mocked version
        from utils.time.get_timeout_message import get_timeout_message as mocked_function
        
        result = mocked_function(30.0, "Test Process")
        assert result == ""
