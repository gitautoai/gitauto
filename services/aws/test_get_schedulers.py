# Standard imports
from unittest.mock import patch

# Third party imports
import pytest
from botocore.exceptions import ClientError, BotoCoreError

# Local imports
from services.aws.get_schedulers import get_schedulers_by_owner_id


@pytest.fixture
def mock_scheduler_client():
    """Fixture to mock the scheduler_client."""
    with patch("services.aws.get_schedulers.scheduler_client") as mock:
        yield mock


def test_get_schedulers_by_owner_id_success_single_page(mock_scheduler_client):
    """Test successful retrieval of schedulers with single page response."""
    # Setup
    owner_id = 123
    mock_response = {
        "Schedules": [
            {"Name": "gitauto-repo-123-456"},
            {"Name": "gitauto-repo-123-789"},
            {"Name": "other-schedule-123"},
            {"Name": "gitauto-repo-456-123"},  # Different owner_id
        ]
    }
    mock_scheduler_client.list_schedules.return_value = mock_response

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    expected = ["gitauto-repo-123-456", "gitauto-repo-123-789"]
    assert result == expected
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_success_multiple_pages(mock_scheduler_client):
    """Test successful retrieval of schedulers with pagination."""
    # Setup
    owner_id = 123
    first_response = {
        "Schedules": [
            {"Name": "gitauto-repo-123-456"},
            {"Name": "gitauto-repo-123-789"},
        ],
        "NextToken": "token123",
    }
    second_response = {
        "Schedules": [
            {"Name": "gitauto-repo-123-101"},
            {"Name": "other-schedule-456"},
        ]
    }
    mock_scheduler_client.list_schedules.side_effect = [first_response, second_response]

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    expected = ["gitauto-repo-123-456", "gitauto-repo-123-789", "gitauto-repo-123-101"]
    assert result == expected
    assert mock_scheduler_client.list_schedules.call_count == 2
    mock_scheduler_client.list_schedules.assert_any_call()
    mock_scheduler_client.list_schedules.assert_any_call(NextToken="token123")


def test_get_schedulers_by_owner_id_empty_response(mock_scheduler_client):
    """Test retrieval when no schedules are returned."""
    # Setup
    owner_id = 123
    mock_response = {"Schedules": []}
    mock_scheduler_client.list_schedules.return_value = mock_response

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    assert not result
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_no_matching_schedules(mock_scheduler_client):
    """Test retrieval when no schedules match the owner_id pattern."""
    # Setup
    owner_id = 123
    mock_response = {
        "Schedules": [
            {"Name": "gitauto-repo-456-789"},
            {"Name": "other-schedule-123"},
            {"Name": "random-schedule"},
        ]
    }
    mock_scheduler_client.list_schedules.return_value = mock_response

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    assert not result
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_missing_schedules_key(mock_scheduler_client):
    """Test retrieval when response doesn't contain 'Schedules' key."""
    # Setup
    owner_id = 123
    mock_response = {}
    mock_scheduler_client.list_schedules.return_value = mock_response

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    assert not result
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_schedule_without_name(mock_scheduler_client):
    """Test retrieval when schedule doesn't have 'Name' key."""
    # Setup
    owner_id = 123
    mock_response = {
        "Schedules": [
            {"Name": "gitauto-repo-123-456"},
            {},  # Schedule without Name key
            {"Name": "gitauto-repo-123-789"},
        ]
    }
    mock_scheduler_client.list_schedules.return_value = mock_response

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    expected = ["gitauto-repo-123-456", "gitauto-repo-123-789"]
    assert result == expected
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_with_index_pattern(mock_scheduler_client):
    """Test retrieval of schedules with index pattern (gitauto-repo-{ownerId}-{repoId}-{index})."""
    # Setup
    owner_id = 123
    mock_response = {
        "Schedules": [
            {"Name": "gitauto-repo-123-456"},
            {"Name": "gitauto-repo-123-456-1"},
            {"Name": "gitauto-repo-123-456-2"},
            {"Name": "gitauto-repo-123-789-0"},
        ]
    }
    mock_scheduler_client.list_schedules.return_value = mock_response

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    expected = [
        "gitauto-repo-123-456",
        "gitauto-repo-123-456-1",
        "gitauto-repo-123-456-2",
        "gitauto-repo-123-789-0",
    ]
    assert result == expected
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_client_error(mock_scheduler_client):
    """Test retrieval when ClientError occurs."""
    # Setup
    owner_id = 123
    mock_scheduler_client.list_schedules.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
        "ListSchedules",
    )

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert - should return default value [] due to handle_exceptions decorator
    assert not result
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_botocore_error(mock_scheduler_client):
    """Test retrieval when BotoCoreError occurs."""
    # Setup
    owner_id = 123
    mock_scheduler_client.list_schedules.side_effect = BotoCoreError()

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert - should return default value [] due to handle_exceptions decorator
    assert not result
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_generic_exception(mock_scheduler_client):
    """Test retrieval when generic exception occurs."""
    # Setup
    owner_id = 123
    mock_scheduler_client.list_schedules.side_effect = Exception("Unexpected error")

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert - should return default value [] due to handle_exceptions decorator
    assert not result
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_exception_during_pagination(mock_scheduler_client):
    """Test retrieval when exception occurs during pagination."""
    # Setup
    owner_id = 123
    first_response = {
        "Schedules": [{"Name": "gitauto-repo-123-456"}],
        "NextToken": "token123",
    }
    mock_scheduler_client.list_schedules.side_effect = [
        first_response,
        Exception("Error on second page"),
    ]

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert - should return default value [] due to handle_exceptions decorator
    assert not result
    assert mock_scheduler_client.list_schedules.call_count == 2


@pytest.mark.parametrize(
    "owner_id,expected_prefix",
    [
        (123, "gitauto-repo-123-"),
        (0, "gitauto-repo-0-"),
        (999999, "gitauto-repo-999999-"),
        (1, "gitauto-repo-1-"),
    ],
)
def test_get_schedulers_by_owner_id_various_owner_ids(
    mock_scheduler_client, owner_id, expected_prefix
):
    """Test retrieval with various owner_id values."""
    # Setup
    mock_response = {
        "Schedules": [
            {"Name": f"{expected_prefix}456"},
            {"Name": f"{expected_prefix}789"},
            {"Name": "gitauto-repo-999-123"},  # Different owner_id
        ]
    }
    mock_scheduler_client.list_schedules.return_value = mock_response

    # Execute
    result = get_schedulers_by_owner_id(owner_id)

    # Assert
    expected = [f"{expected_prefix}456", f"{expected_prefix}789"]
    assert result == expected
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_get_schedulers_by_owner_id_handle_exceptions_decorator():
    """Test that the function has the correct handle_exceptions decorator configuration."""
    # This test verifies the decorator is applied with correct parameters
    # by checking the function's behavior when an exception occurs
    with patch("services.aws.get_schedulers.scheduler_client") as mock_client:
        mock_client.list_schedules.side_effect = Exception("Test exception")

        result = get_schedulers_by_owner_id(123)

        # Should return [] (default_return_value) and not raise exception (raise_on_error=False)
        assert not result
