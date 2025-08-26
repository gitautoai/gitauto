import asyncio
import logging
import time
from unittest.mock import patch, MagicMock
import pytest

from utils.time.timer import timer_decorator


class TestTimerDecorator:
    """Test cases for the timer_decorator function."""

    @pytest.fixture
    def mock_logger(self):
        """Mock the logger to capture log messages."""
        with patch('utils.time.timer.logger') as mock_log:
            yield mock_log

    @pytest.fixture
    def mock_time(self):
        """Mock time.time() to control timing measurements."""
        with patch('utils.time.timer.time.time') as mock_t:
            # Set up mock to return predictable time values
            mock_t.side_effect = [1000.0, 1002.5]  # 2.5 second difference
            yield mock_t

    def test_timer_decorator_with_sync_function(self, mock_logger, mock_time):
        """Test timer decorator with synchronous function."""
        @timer_decorator
        def sample_sync_function(x, y):
            return x + y

        result = sample_sync_function(3, 4)

        assert result == 7
        mock_time.assert_called()
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "sample_sync_function", 2.5
        )

    def test_timer_decorator_with_sync_function_args_kwargs(self, mock_logger, mock_time):
        """Test timer decorator with sync function using args and kwargs."""
        @timer_decorator
        def sample_function(a, b, c=None, d=None):
            return f"{a}-{b}-{c}-{d}"

        result = sample_function(1, 2, c=3, d=4)

        assert result == "1-2-3-4"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "sample_function", 2.5
        )

    @pytest.mark.asyncio
    async def test_timer_decorator_with_async_function(self, mock_logger, mock_time):
        """Test timer decorator with asynchronous function."""
        @timer_decorator
        async def sample_async_function(x, y):
            await asyncio.sleep(0)  # Simulate async operation
            return x * y

        result = await sample_async_function(3, 4)

        assert result == 12
        mock_time.assert_called()
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "sample_async_function", 2.5
        )

    @pytest.mark.asyncio
    async def test_timer_decorator_with_async_function_args_kwargs(self, mock_logger, mock_time):
        """Test timer decorator with async function using args and kwargs."""
        @timer_decorator
        async def sample_async_function(a, b, c=None, d=None):
            await asyncio.sleep(0)  # Simulate async operation
            return f"{a}+{b}+{c}+{d}"

        result = await sample_async_function(1, 2, c=3, d=4)

        assert result == "1+2+3+4"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "sample_async_function", 2.5
        )

    def test_timer_decorator_preserves_function_metadata(self):
        """Test that timer decorator preserves original function metadata."""
        @timer_decorator
        def original_function():
            """Original function docstring."""
            return "test"

        assert original_function.__name__ == "original_function"
        assert original_function.__doc__ == "Original function docstring."

    @pytest.mark.asyncio
    async def test_timer_decorator_preserves_async_function_metadata(self):
        """Test that timer decorator preserves async function metadata."""
        @timer_decorator
        async def original_async_function():
            """Original async function docstring."""
            return "async_test"

        assert original_async_function.__name__ == "original_async_function"
        assert original_async_function.__doc__ == "Original async function docstring."

    def test_timer_decorator_with_exception_in_sync_function(self, mock_logger, mock_time):
        """Test timer decorator when sync function raises exception - timing not logged."""
        @timer_decorator
        def failing_function():
            raise ValueError("Test exception")

        with pytest.raises(ValueError, match="Test exception"):
            failing_function()

        # Current implementation doesn't log timing when exception occurs
        # because the logging happens after the function call
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_timer_decorator_with_exception_in_async_function(self, mock_logger, mock_time):
        """Test timer decorator when async function raises exception - timing not logged."""
        @timer_decorator
        async def failing_async_function():
            raise ValueError("Async test exception")

        with pytest.raises(ValueError, match="Async test exception"):
            await failing_async_function()

        # Current implementation doesn't log timing when exception occurs
        # because the logging happens after the function call
        mock_logger.info.assert_not_called()

    def test_timer_decorator_with_no_args_sync_function(self, mock_logger, mock_time):
        """Test timer decorator with sync function that takes no arguments."""
        @timer_decorator
        def no_args_function():
            return "no args"

        result = no_args_function()

        assert result == "no args"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "no_args_function", 2.5
        )

    @pytest.mark.asyncio
    async def test_timer_decorator_with_no_args_async_function(self, mock_logger, mock_time):
        """Test timer decorator with async function that takes no arguments."""
        @timer_decorator
        async def no_args_async_function():
            await asyncio.sleep(0)
            return "no args async"

        result = await no_args_async_function()

        assert result == "no args async"
        mock_logger.info.assert_called_once_with(
            "%s took %.2f seconds", "no_args_async_function", 2.5
        )

    def test_timer_decorator_with_different_time_values(self, mock_logger):
        """Test timer decorator with different timing scenarios."""
        with patch('utils.time.timer.time.time') as mock_t:
            # Test with very short execution time
            mock_t.side_effect = [1000.0, 1000.01]  # 0.01 second difference
            
            @timer_decorator
            def quick_function():
                return "quick"

            result = quick_function()

            assert result == "quick"
            mock_logger.info.assert_called_once_with(
                "%s took %.2f seconds", "quick_function", 0.01
            )

    @pytest.mark.asyncio
    async def test_timer_decorator_async_with_different_time_values(self, mock_logger):
        """Test timer decorator with async function and different timing scenarios."""
        with patch('utils.time.timer.time.time') as mock_t:
            # Test with longer execution time
            mock_t.side_effect = [1000.0, 1005.75]  # 5.75 second difference
            
            @timer_decorator
            async def slow_async_function():
                await asyncio.sleep(0)
                return "slow async"

            result = await slow_async_function()

            assert result == "slow async"
            mock_logger.info.assert_called_once_with(
                "%s took %.2f seconds", "slow_async_function", 5.75
            )