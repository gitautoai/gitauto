import asyncio
import functools
import inspect
import time
from unittest.mock import patch, MagicMock

import pytest

from utils.time.timer import timer_decorator


@pytest.fixture
def mock_time():
    """Fixture to mock time.time() for consistent testing."""
    with patch("utils.time.timer.time.time") as mock:
        # Return predictable time values: start=1.0, end=3.0 (2 second duration)
        mock.side_effect = [1.0, 3.0]
        yield mock


@pytest.fixture
def mock_logger():
    """Fixture to mock the logger for testing log output."""
    with patch("utils.time.timer.logger") as mock:
        yield mock


def test_timer_decorator_with_sync_function(mock_time, mock_logger):
    """Test timer decorator with synchronous function."""
    @timer_decorator
    def sync_function(x, y):
        return x + y

    result = sync_function(2, 3)

    assert result == 5
    assert mock_time.call_count == 2
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "sync_function", 2.0
    )


def test_timer_decorator_with_async_function(mock_time, mock_logger):
    """Test timer decorator with asynchronous function."""
    @timer_decorator
    async def async_function(x, y):
        return x * y

    async def run_test():
        result = await async_function(4, 5)
        return result

    result = asyncio.run(run_test())

    assert result == 20
    assert mock_time.call_count == 2
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "async_function", 2.0
    )


def test_timer_decorator_preserves_function_metadata():
    """Test that timer decorator preserves original function metadata."""
    def original_function():
        """Original function docstring."""
        return "test"

    decorated_function = timer_decorator(original_function)

    assert decorated_function.__name__ == "original_function"
    assert decorated_function.__doc__ == "Original function docstring."
    assert hasattr(decorated_function, "__wrapped__")
    assert decorated_function.__wrapped__ is original_function


def test_timer_decorator_with_function_arguments(mock_time, mock_logger):
    """Test timer decorator with function that takes arguments."""
    @timer_decorator
    def function_with_args(a, b, c=None, *args, **kwargs):
        return {"a": a, "b": b, "c": c, "args": args, "kwargs": kwargs}

    result = function_with_args(1, 2, 3, 4, 5, key="value")

    expected = {"a": 1, "b": 2, "c": 3, "args": (4, 5), "kwargs": {"key": "value"}}
    assert result == expected
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "function_with_args", 2.0
    )


def test_timer_decorator_with_async_function_arguments(mock_time, mock_logger):
    """Test timer decorator with async function that takes arguments."""
    @timer_decorator
    async def async_function_with_args(a, b, c=None, *args, **kwargs):
        return {"a": a, "b": b, "c": c, "args": args, "kwargs": kwargs}

    async def run_test():
        result = await async_function_with_args(1, 2, c=3, extra1=4, extra2=5, key="value")
        return result

    result = asyncio.run(run_test())

    expected = {"a": 1, "b": 2, "c": 3, "args": (), "kwargs": {"extra1": 4, "extra2": 5, "key": "value"}}
    assert result == expected
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "async_function_with_args", 2.0
    )


def test_timer_decorator_with_function_that_raises_exception(mock_time, mock_logger):
    """Test timer decorator with function that raises an exception."""
    @timer_decorator
    def function_that_raises():
        raise ValueError("Test exception")

    with pytest.raises(ValueError, match="Test exception"):
        function_that_raises()

    # Should still log the time even when exception is raised
    assert mock_time.call_count == 2
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "function_that_raises", 2.0
    )


def test_timer_decorator_with_async_function_that_raises_exception(mock_time, mock_logger):
    """Test timer decorator with async function that raises an exception."""
    @timer_decorator
    async def async_function_that_raises():
        raise ValueError("Test async exception")

    async def run_test():
        await async_function_that_raises()

    with pytest.raises(ValueError, match="Test async exception"):
        asyncio.run(run_test())

    # Should still log the time even when exception is raised
    assert mock_time.call_count == 2
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "async_function_that_raises", 2.0
    )


def test_timer_decorator_detects_coroutine_function():
    """Test that timer decorator correctly detects coroutine functions."""
    async def async_func():
        return "async"

    def sync_func():
        return "sync"

    # Test that inspect.iscoroutinefunction works as expected
    assert inspect.iscoroutinefunction(async_func) is True
    assert inspect.iscoroutinefunction(sync_func) is False

    # Apply decorator
    decorated_async = timer_decorator(async_func)
    decorated_sync = timer_decorator(sync_func)

    # Decorated async function should still be a coroutine function
    assert inspect.iscoroutinefunction(decorated_async) is True
    assert inspect.iscoroutinefunction(decorated_sync) is False


def test_timer_decorator_with_zero_execution_time(mock_logger):
    """Test timer decorator when execution time is zero."""
    with patch("utils.time.timer.time.time") as mock_time:
        # Both calls return the same time (zero duration)
        mock_time.side_effect = [1.0, 1.0]

        @timer_decorator
        def instant_function():
            return "instant"

        result = instant_function()

        assert result == "instant"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "instant_function", 0.0
        )


def test_timer_decorator_with_very_long_execution_time(mock_logger):
    """Test timer decorator with very long execution time."""
    with patch("utils.time.timer.time.time") as mock_time:
        # Simulate 100.5 second execution
        mock_time.side_effect = [1.0, 101.5]

        @timer_decorator
        def long_function():
            return "long"

        result = long_function()

        assert result == "long"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "long_function", 100.5
        )


def test_timer_decorator_with_fractional_seconds(mock_logger):
    """Test timer decorator with fractional seconds."""
    with patch("utils.time.timer.time.time") as mock_time:
        # Simulate 1.234567 second execution
        mock_time.side_effect = [1.0, 2.234567]

        @timer_decorator
        def fractional_function():
            return "fractional"

        result = fractional_function()

        assert result == "fractional"
        # Should be rounded to 2 decimal places
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "fractional_function", 1.23
        )


def test_timer_decorator_multiple_calls(mock_logger):
    """Test timer decorator with multiple function calls."""
    with patch("utils.time.timer.time.time") as mock_time:
        # First call: 1.0 -> 2.0 (1 second)
        # Second call: 3.0 -> 5.5 (2.5 seconds)
        mock_time.side_effect = [1.0, 2.0, 3.0, 5.5]

        @timer_decorator
        def multi_call_function(value):
            return value * 2

        result1 = multi_call_function(5)
        result2 = multi_call_function(10)

        assert result1 == 10
        assert result2 == 20
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call(
            "%s took %.2f seconds", "multi_call_function", 1.0
        )
        mock_logger.info.assert_any_call(
            "%s took %.2f seconds", "multi_call_function", 2.5
        )
