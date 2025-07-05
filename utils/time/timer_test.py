import asyncio
import time
from unittest.mock import patch, MagicMock
import pytest
from utils.time.timer import timer_decorator


@pytest.fixture
def mock_logger():
    """Mock logger to capture log messages."""
    with patch("utils.time.timer.logger") as mock:
        yield mock


@pytest.fixture
def mock_time():
    """Mock time.time() to control timing measurements."""
    with patch("utils.time.timer.time") as mock:
        # Set up a sequence of time values: start=1.0, end=3.5 (2.5 seconds elapsed)
        mock.time.side_effect = [1.0, 3.5]
        yield mock


def test_timer_decorator_sync_function_execution(mock_logger, mock_time):
    """Test that timer decorator works with synchronous functions."""
    @timer_decorator
    def sample_function(x, y):
        return x + y
    
    result = sample_function(2, 3)
    
    assert result == 5
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "sample_function", 2.5
    )


def test_timer_decorator_sync_function_with_args_kwargs(mock_logger, mock_time):
    """Test that timer decorator preserves function arguments and keyword arguments."""
    @timer_decorator
    def sample_function(a, b, c=None, d=None):
        return f"{a}-{b}-{c}-{d}"
    
    result = sample_function("hello", "world", c="test", d="value")
    
    assert result == "hello-world-test-value"
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "sample_function", 2.5
    )


def test_timer_decorator_sync_function_exception_handling(mock_logger, mock_time):
    """Test that timer decorator handles exceptions in synchronous functions."""
    @timer_decorator
    def failing_function():
        raise ValueError("Test exception")
    
    with pytest.raises(ValueError, match="Test exception"):
        failing_function()
    
    # Logger should still be called even when function raises exception
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "failing_function", 2.5
    )


@pytest.mark.asyncio
async def test_timer_decorator_async_function_execution(mock_logger, mock_time):
    """Test that timer decorator works with asynchronous functions."""
    @timer_decorator
    async def async_sample_function(x, y):
        return x * y
    
    result = await async_sample_function(4, 5)
    
    assert result == 20
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "async_sample_function", 2.5
    )


@pytest.mark.asyncio
async def test_timer_decorator_async_function_with_args_kwargs(mock_logger, mock_time):
    """Test that timer decorator preserves async function arguments and keyword arguments."""
    @timer_decorator
    async def async_sample_function(a, b=None, c=None):
        await asyncio.sleep(0)  # Simulate async operation
        return f"{a}:{b}:{c}"
    
    result = await async_sample_function("test", b="param", c="value")
    
    assert result == "test:param:value"
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "async_sample_function", 2.5
    )


@pytest.mark.asyncio
async def test_timer_decorator_async_function_exception_handling(mock_logger, mock_time):
    """Test that timer decorator handles exceptions in asynchronous functions."""
    @timer_decorator
    async def failing_async_function():
        raise RuntimeError("Async test exception")
    
    with pytest.raises(RuntimeError, match="Async test exception"):
        await failing_async_function()
    
    # Logger should still be called even when async function raises exception
    mock_logger.info.assert_called_once_with(
        "%s took %.2f seconds", "failing_async_function", 2.5
    )


def test_timer_decorator_preserves_function_metadata():
    """Test that timer decorator preserves original function metadata using functools.wraps."""
    def original_function():
        """Original function docstring."""
        pass
    
    original_function.__custom_attr__ = "custom_value"
    
    decorated_function = timer_decorator(original_function)
    
    assert decorated_function.__name__ == "original_function"
    assert decorated_function.__doc__ == "Original function docstring."
    assert hasattr(decorated_function, "__custom_attr__")
    assert decorated_function.__custom_attr__ == "custom_value"


@pytest.mark.asyncio
async def test_timer_decorator_preserves_async_function_metadata():
    """Test that timer decorator preserves async function metadata using functools.wraps."""
    async def original_async_function():
        """Original async function docstring."""
        pass
    
    original_async_function.__custom_attr__ = "async_custom_value"
    
    decorated_function = timer_decorator(original_async_function)
    
    assert decorated_function.__name__ == "original_async_function"
    assert decorated_function.__doc__ == "Original async function docstring."
    assert hasattr(decorated_function, "__custom_attr__")
    assert decorated_function.__custom_attr__ == "async_custom_value"


def test_timer_decorator_different_timing_values():
    """Test timer decorator with different timing scenarios."""
    with patch("utils.time.timer.time") as mock_time_module:
        with patch("utils.time.timer.logger") as mock_logger:
            # Test very short execution time
            mock_time_module.time.side_effect = [10.0, 10.01]  # 0.01 seconds
            
            @timer_decorator
            def quick_function():
                return "quick"
            
            result = quick_function()
            
            assert result == "quick"
            mock_logger.info.assert_called_once_with(
                "%s took %.2f seconds", "quick_function", 0.01
            )


def test_timer_decorator_zero_execution_time():
    """Test timer decorator when execution time is effectively zero."""
    with patch("utils.time.timer.time") as mock_time_module:
        with patch("utils.time.timer.logger") as mock_logger:
            # Same start and end time
            mock_time_module.time.side_effect = [5.0, 5.0]  # 0.0 seconds
            
            @timer_decorator
            def instant_function():
                return "instant"
            
            result = instant_function()
            
            assert result == "instant"
            mock_logger.info.assert_called_once_with(
                "%s took %.2f seconds", "instant_function", 0.0
            )


def test_timer_decorator_function_detection():
    """Test that timer decorator correctly detects sync vs async functions."""
    # Test with regular function
    @timer_decorator
    def sync_func():
        return "sync"
    
    # Test with async function
    @timer_decorator
    async def async_func():
        return "async"
    
    # Verify the decorated functions maintain their sync/async nature
    assert not asyncio.iscoroutinefunction(sync_func)
    assert asyncio.iscoroutinefunction(async_func)


def test_timer_decorator_multiple_calls():
    """Test that timer decorator works correctly with multiple function calls."""
    call_times = [
        [1.0, 2.0],  # First call: 1.0 second
        [3.0, 3.5],  # Second call: 0.5 seconds
        [4.0, 6.0],  # Third call: 2.0 seconds
    ]
    
    with patch("utils.time.timer.time") as mock_time_module:
        with patch("utils.time.timer.logger") as mock_logger:
            
            @timer_decorator
            def multi_call_function(value):
                return value * 2
            
            # Make multiple calls
            for i, times in enumerate(call_times):
                mock_time_module.time.side_effect = times
                result = multi_call_function(i + 1)
                assert result == (i + 1) * 2
            
            # Verify all calls were logged
            assert mock_logger.info.call_count == 3
            expected_calls = [
                (("%s took %.2f seconds", "multi_call_function", 1.0),),
                (("%s took %.2f seconds", "multi_call_function", 0.5),),
                (("%s took %.2f seconds", "multi_call_function", 2.0),),
            ]
            
            actual_calls = [call.args for call in mock_logger.info.call_args_list]
            assert actual_calls == expected_calls
