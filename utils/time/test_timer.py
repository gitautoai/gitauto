import asyncio
import functools
import inspect
import logging
import time
from unittest.mock import patch, MagicMock

import pytest

from utils.time.timer import timer_decorator


@pytest.fixture
def mock_logger():
    """Fixture to mock the logger."""
    with patch("utils.time.timer.logger") as mock:
        yield mock


@pytest.fixture
def mock_time():
    """Fixture to mock time.time() for consistent timing tests."""
    with patch("utils.time.timer.time") as mock:
        # Set up predictable time values
        mock.time.side_effect = [1000.0, 1002.5]  # 2.5 second difference
        yield mock


class TestTimerDecoratorSync:
    """Test timer_decorator with synchronous functions."""

    def test_sync_function_execution_and_timing(self, mock_logger, mock_time):
        """Test that sync function executes correctly and logs timing."""
        @timer_decorator
        def test_function(x, y):
            return x + y

        result = test_function(3, 4)

        assert result == 7
        mock_time.time.assert_called()
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "test_function", 2.5
        )

    def test_sync_function_with_no_args(self, mock_logger, mock_time):
        """Test sync function with no arguments."""
        @timer_decorator
        def no_args_function():
            return "success"

        result = no_args_function()

        assert result == "success"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "no_args_function", 2.5
        )

    def test_sync_function_with_kwargs(self, mock_logger, mock_time):
        """Test sync function with keyword arguments."""
        @timer_decorator
        def kwargs_function(a, b=10, c=20):
            return a + b + c

        result = kwargs_function(5, c=15)

        assert result == 30
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "kwargs_function", 2.5
        )

    def test_sync_function_exception_handling(self, mock_logger, mock_time):
        """Test that exceptions are properly propagated and timing still occurs."""
        @timer_decorator
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Should still log timing even when exception occurs
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "failing_function", 2.5
        )

    def test_sync_function_metadata_preservation(self):
        """Test that function metadata is preserved."""
        @timer_decorator
        def documented_function(x):
            """This is a test function."""
            return x * 2

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."
        assert hasattr(documented_function, "__wrapped__")


class TestTimerDecoratorAsync:
    """Test timer_decorator with asynchronous functions."""

    @pytest.mark.asyncio
    async def test_async_function_execution_and_timing(self, mock_logger, mock_time):
        """Test that async function executes correctly and logs timing."""
        @timer_decorator
        async def async_test_function(x, y):
            return x * y

        result = await async_test_function(6, 7)

        assert result == 42
        mock_time.time.assert_called()
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "async_test_function", 2.5
        )

    @pytest.mark.asyncio
    async def test_async_function_with_no_args(self, mock_logger, mock_time):
        """Test async function with no arguments."""
        @timer_decorator
        async def async_no_args():
            return "async_success"

        result = await async_no_args()

        assert result == "async_success"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "async_no_args", 2.5
        )

    @pytest.mark.asyncio
    async def test_async_function_with_kwargs(self, mock_logger, mock_time):
        """Test async function with keyword arguments."""
        @timer_decorator
        async def async_kwargs_function(a, b=5, c=10):
            await asyncio.sleep(0)  # Simulate async operation
            return a + b + c

        result = await async_kwargs_function(1, c=3)

        assert result == 9
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "async_kwargs_function", 2.5
        )

    @pytest.mark.asyncio
    async def test_async_function_exception_handling(self, mock_logger, mock_time):
        """Test that exceptions are properly propagated in async functions."""
        @timer_decorator
        async def async_failing_function():
            raise RuntimeError("Async test error")

        with pytest.raises(RuntimeError, match="Async test error"):
            await async_failing_function()

        # Should still log timing even when exception occurs
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "async_failing_function", 2.5
        )

    @pytest.mark.asyncio
    async def test_async_function_metadata_preservation(self):
        """Test that async function metadata is preserved."""
        @timer_decorator
        async def async_documented_function(x):
            """This is an async test function."""
            return x ** 2

        assert async_documented_function.__name__ == "async_documented_function"
        assert async_documented_function.__doc__ == "This is an async test function."
        assert hasattr(async_documented_function, "__wrapped__")


class TestTimerDecoratorEdgeCases:
    """Test edge cases and special scenarios."""

    def test_function_with_none_return(self, mock_logger, mock_time):
        """Test function that returns None."""
        @timer_decorator
        def none_return_function():
            pass

        result = none_return_function()

        assert result is None
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "none_return_function", 2.5
        )

    def test_timing_precision(self, mock_logger):
        """Test that timing precision is maintained."""
        with patch("utils.time.timer.time") as mock_time:
            mock_time.time.side_effect = [1000.123456, 1000.987654]  # 0.864198 seconds

            @timer_decorator
            def precision_function():
                return "precise"

            precision_function()

            mock_logger.info.assert_called_once_with(
                "%s took %.2f seconds", "precision_function", 0.86
            )

    def test_multiple_decorations(self, mock_logger, mock_time):
        """Test that timer_decorator works with multiple decorations."""
        def another_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        @timer_decorator
        @another_decorator
        def multi_decorated_function():
            return "decorated"

        result = multi_decorated_function()

        assert result == "decorated"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "multi_decorated_function", 2.5
        )

    def test_function_inspection_detection(self):
        """Test that inspect.iscoroutinefunction correctly identifies function types."""
        def sync_func():
            pass

        async def async_func():
            pass

        # Test that our decorator correctly identifies function types
        assert not inspect.iscoroutinefunction(sync_func)
        assert inspect.iscoroutinefunction(async_func)

        # Test decorated functions
        decorated_sync = timer_decorator(sync_func)
        decorated_async = timer_decorator(async_func)

        # Sync function should not be a coroutine function after decoration
        assert not inspect.iscoroutinefunction(decorated_sync)
        # Async function should still be a coroutine function after decoration
        assert inspect.iscoroutinefunction(decorated_async)

    def test_zero_execution_time(self, mock_logger):
        """Test behavior when execution time is exactly zero."""
        with patch("utils.time.timer.time") as mock_time:
            mock_time.time.side_effect = [1000.0, 1000.0]  # Same time

            @timer_decorator
            def instant_function():
                return "instant"

            result = instant_function()

            assert result == "instant"
            mock_logger.info.assert_called_once_with(
                "%s took %.2f seconds", "instant_function", 0.0
            )

    def test_logger_module_name(self):
        """Test that logger is created with correct module name."""
        from utils.time.timer import logger
        assert logger.name == "utils.time.timer"
