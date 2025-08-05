# Standard imports
from unittest.mock import patch, MagicMock
import logging

# Third party imports
import pytest
from botocore.exceptions import ClientError, BotoCoreError

# Local imports
from services.aws.delete_scheduler import delete_scheduler


@pytest.fixture
def mock_scheduler_client():
    """Fixture to mock the scheduler_client."""
    with patch("services.aws.delete_scheduler.scheduler_client") as mock:
        yield mock


@pytest.fixture
def mock_logging():
    """Fixture to mock logging."""
    with patch("services.aws.delete_scheduler.logging") as mock:
        yield mock


def test_delete_scheduler_success(mock_scheduler_client, mock_logging):
    """Test successful scheduler deletion."""
    # Setup
    schedule_name = "test-schedule-123"
    mock_scheduler_client.delete_schedule.return_value = None

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert
    assert result is True
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_called_once_with(
        "Deleted EventBridge Scheduler: %s", schedule_name
    )


def test_delete_scheduler_with_empty_schedule_name(mock_scheduler_client, mock_logging):
    """Test scheduler deletion with empty schedule name."""
    # Setup
    schedule_name = ""
    mock_scheduler_client.delete_schedule.return_value = None

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert
    assert result is True
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_called_once_with(
        "Deleted EventBridge Scheduler: %s", schedule_name
    )


def test_delete_scheduler_with_special_characters(mock_scheduler_client, mock_logging):
    """Test scheduler deletion with special characters in name."""
    # Setup
    schedule_name = "test-schedule_with.special@chars#123"
    mock_scheduler_client.delete_schedule.return_value = None

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert
    assert result is True
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_called_once_with(
        "Deleted EventBridge Scheduler: %s", schedule_name
    )


def test_delete_scheduler_client_error_resource_not_found(mock_scheduler_client, mock_logging):
    """Test scheduler deletion when resource is not found."""
    # Setup
    schedule_name = "non-existent-schedule"
    error_response = {"Error": {"Code": "ResourceNotFoundException", "Message": "Schedule not found"}}
    mock_scheduler_client.delete_schedule.side_effect = ClientError(
        error_response, "DeleteSchedule"
    )

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert - should return False due to handle_exceptions decorator
    assert result is False
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    # Logging should not be called when exception occurs
    mock_logging.info.assert_not_called()


def test_delete_scheduler_client_error_access_denied(mock_scheduler_client, mock_logging):
    """Test scheduler deletion when access is denied."""
    # Setup
    schedule_name = "restricted-schedule"
    error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
    mock_scheduler_client.delete_schedule.side_effect = ClientError(
        error_response, "DeleteSchedule"
    )

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert - should return False due to handle_exceptions decorator
    assert result is False
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_not_called()


def test_delete_scheduler_client_error_throttling(mock_scheduler_client, mock_logging):
    """Test scheduler deletion when throttling occurs."""
    # Setup
    schedule_name = "throttled-schedule"
    error_response = {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}}
    mock_scheduler_client.delete_schedule.side_effect = ClientError(
        error_response, "DeleteSchedule"
    )

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert - should return False due to handle_exceptions decorator
    assert result is False
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_not_called()


def test_delete_scheduler_botocore_error(mock_scheduler_client, mock_logging):
    """Test scheduler deletion with BotoCoreError."""
    # Setup
    schedule_name = "error-schedule"
    mock_scheduler_client.delete_schedule.side_effect = BotoCoreError()

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert - should return False due to handle_exceptions decorator
    assert result is False
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_not_called()


def test_delete_scheduler_generic_exception(mock_scheduler_client, mock_logging):
    """Test scheduler deletion with generic exception."""
    # Setup
    schedule_name = "exception-schedule"
    mock_scheduler_client.delete_schedule.side_effect = Exception("Unexpected error")

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert - should return False due to handle_exceptions decorator
    assert result is False
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_not_called()


def test_delete_scheduler_with_none_schedule_name(mock_scheduler_client, mock_logging):
    """Test scheduler deletion with None schedule name."""
    # Setup
    schedule_name = None
    mock_scheduler_client.delete_schedule.return_value = None

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert
    assert result is True
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_called_once_with(
        "Deleted EventBridge Scheduler: %s", schedule_name
    )


@pytest.mark.parametrize(
    "schedule_name",
    [
        "simple-schedule",
        "gitauto-repo-123-456",
        "schedule_with_underscores",
        "schedule-with-dashes",
        "schedule.with.dots",
        "UPPERCASE-SCHEDULE",
        "MixedCase-Schedule_123",
        "very-long-schedule-name-with-many-characters-1234567890",
    ],
)
def test_delete_scheduler_with_various_schedule_names(
    mock_scheduler_client, mock_logging, schedule_name
):
    """Test scheduler deletion with various schedule name formats."""
    # Setup
    mock_scheduler_client.delete_schedule.return_value = None

    # Execute
    result = delete_scheduler(schedule_name)

    # Assert
    assert result is True
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    mock_logging.info.assert_called_once_with(
        "Deleted EventBridge Scheduler: %s", schedule_name
    )


def test_delete_scheduler_logging_level(mock_scheduler_client):
    """Test that the function uses logging.info for success messages."""
    schedule_name = "test-schedule"
    mock_scheduler_client.delete_schedule.return_value = None
    
    with patch("services.aws.delete_scheduler.logging.info") as mock_info:
        result = delete_scheduler(schedule_name)
        
        assert result is True
        mock_info.assert_called_once_with(
            "Deleted EventBridge Scheduler: %s", schedule_name
        )


def test_delete_scheduler_client_method_call_parameters(mock_scheduler_client, mock_logging):
    """Test that scheduler_client.delete_schedule is called with correct parameters."""
    schedule_name = "test-schedule-params"
    mock_scheduler_client.delete_schedule.return_value = None
    
    delete_scheduler(schedule_name)
    
    # Verify the exact method call
    mock_scheduler_client.delete_schedule.assert_called_once()
    call_args = mock_scheduler_client.delete_schedule.call_args
    assert call_args[1]["Name"] == schedule_name  # Keyword argument
    assert len(call_args[1]) == 1  # Only one parameter


def test_delete_scheduler_exception_before_logging(mock_scheduler_client, mock_logging):
    """Test that logging is not called when exception occurs before logging."""
    schedule_name = "exception-before-log"
    # Exception occurs during delete_schedule call, before logging
    mock_scheduler_client.delete_schedule.side_effect = Exception("AWS Error")
    
    result = delete_scheduler(schedule_name)
    
    # Should return False due to handle_exceptions decorator
    assert result is False
    mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
    # Logging should not be called since exception occurred before it
    mock_logging.info.assert_not_called()

