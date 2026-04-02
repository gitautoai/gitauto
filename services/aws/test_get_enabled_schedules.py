# pylint: disable=redefined-outer-name, unused-argument
# Standard imports
from unittest.mock import patch

# Third party imports
import pytest
from botocore.exceptions import BotoCoreError, ClientError
# Local imports
from services.aws.get_enabled_schedules import get_enabled_schedules


@pytest.fixture
def mock_scheduler_client():
    """Fixture to mock the scheduler_client used by get_enabled_schedules."""
    with patch("services.aws.get_enabled_schedules.scheduler_client") as mock:
        yield mock


def test_single_page_returns_enabled_repo_tuples(mock_scheduler_client):
    # Verifies basic filtering: only ENABLED + gitauto-repo- prefix schedules are returned
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-100-200", "State": "ENABLED"},
            {"Name": "gitauto-repo-100-300", "State": "ENABLED"},
            {"Name": "gitauto-repo-100-400", "State": "DISABLED"},
            {"Name": "other-schedule-100", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == {(100, 200), (100, 300)}
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_pagination_aggregates_across_pages(mock_scheduler_client):
    # Verifies that NextToken-based pagination collects results from all pages
    first_page = {
        "Schedules": [
            {"Name": "gitauto-repo-1-10", "State": "ENABLED"},
        ],
        "NextToken": "page2",
    }
    second_page = {
        "Schedules": [
            {"Name": "gitauto-repo-2-20", "State": "ENABLED"},
        ],
        "NextToken": "page3",
    }
    third_page = {
        "Schedules": [
            {"Name": "gitauto-repo-3-30", "State": "ENABLED"},
        ],
    }
    mock_scheduler_client.list_schedules.side_effect = [
        first_page,
        second_page,
        third_page,
    ]

    result = get_enabled_schedules()

    assert result == {(1, 10), (2, 20), (3, 30)}
    assert mock_scheduler_client.list_schedules.call_count == 3
    mock_scheduler_client.list_schedules.assert_any_call()
    mock_scheduler_client.list_schedules.assert_any_call(NextToken="page2")
    mock_scheduler_client.list_schedules.assert_any_call(NextToken="page3")


def test_empty_schedules_list_returns_empty_set(mock_scheduler_client):
    # Verifies that an empty Schedules array yields an empty set
    mock_scheduler_client.list_schedules.return_value = {"Schedules": []}

    result = get_enabled_schedules()

    assert result == set()
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_missing_schedules_key_returns_empty_set(mock_scheduler_client):
    # Verifies graceful handling when response lacks the "Schedules" key entirely
    mock_scheduler_client.list_schedules.return_value = {}

    result = get_enabled_schedules()

    assert result == set()


def test_disabled_schedules_are_excluded(mock_scheduler_client):
    # Verifies that only ENABLED state is accepted; DISABLED and other states are skipped
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-10-20", "State": "DISABLED"},
            {"Name": "gitauto-repo-10-30", "State": "PAUSED"},
            {"Name": "gitauto-repo-10-40", "State": ""},
        ]
    }

    result = get_enabled_schedules()

    assert result == set()


def test_non_gitauto_prefix_schedules_are_excluded(mock_scheduler_client):
    # Verifies that schedules without the gitauto-repo- prefix are filtered out
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "my-custom-schedule", "State": "ENABLED"},
            {"Name": "gitauto-org-10-20", "State": "ENABLED"},
            {"Name": "repo-gitauto-10-20", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == set()


def test_schedule_missing_state_key_defaults_to_empty_string(mock_scheduler_client):
    # State defaults to "" via .get("State", ""), so missing State means not ENABLED
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-5-6"},
        ]
    }

    result = get_enabled_schedules()

    assert result == set()


def test_schedule_missing_name_key_defaults_to_empty_string(mock_scheduler_client):
    # Name defaults to "" via .get("Name", ""), so missing Name won't match prefix
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == set()


def test_name_with_extra_dashes_uses_first_two_parts(mock_scheduler_client):
    # Names like gitauto-repo-123-456-1 split to ["123", "456", "1"]; only parts[0] and parts[1] used
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-100-200-0", "State": "ENABLED"},
            {"Name": "gitauto-repo-100-200-1", "State": "ENABLED"},
            {"Name": "gitauto-repo-100-300-5", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    # Duplicates collapse in the set: (100, 200) appears once despite two schedule names
    assert result == {(100, 200), (100, 300)}


def test_duplicate_owner_repo_pairs_are_deduplicated(mock_scheduler_client):
    # Multiple schedules for the same owner/repo pair should produce a single tuple in the set
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-42-99", "State": "ENABLED"},
            {"Name": "gitauto-repo-42-99", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == {(42, 99)}


def test_large_owner_and_repo_ids(mock_scheduler_client):
    # Verifies that large integer IDs are parsed correctly
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-999999999-888888888", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == {(999999999, 888888888)}


def test_malformed_name_non_numeric_parts_raises_and_returns_default(
    mock_scheduler_client,
):
    # int("abc") raises ValueError; handle_exceptions catches it and returns set()
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-abc-def", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == set()


def test_malformed_name_empty_after_prefix_raises_and_returns_default(
    mock_scheduler_client,
):
    # "gitauto-repo-" with nothing after → split gives [""], int("") raises ValueError
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == set()


def test_malformed_name_single_part_raises_and_returns_default(mock_scheduler_client):
    # "gitauto-repo-123" → parts = ["123"], parts[1] raises IndexError
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-123", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == set()


def test_client_error_returns_empty_set(mock_scheduler_client):
    # AWS ClientError is caught by handle_exceptions, returning default set()
    mock_scheduler_client.list_schedules.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
        "ListSchedules",
    )

    result = get_enabled_schedules()

    assert result == set()
    mock_scheduler_client.list_schedules.assert_called_once_with()


def test_botocore_error_returns_empty_set(mock_scheduler_client):
    # BotoCoreError is caught by handle_exceptions, returning default set()
    mock_scheduler_client.list_schedules.side_effect = BotoCoreError()

    result = get_enabled_schedules()

    assert result == set()


def test_generic_runtime_error_returns_empty_set(mock_scheduler_client):
    # Any uncaught exception is handled by the decorator, returning default set()
    mock_scheduler_client.list_schedules.side_effect = RuntimeError("Unexpected")

    result = get_enabled_schedules()

    assert result == set()


def test_exception_during_pagination_returns_empty_set(mock_scheduler_client):
    # Error on second page means the decorator catches it and returns default set()
    first_page = {
        "Schedules": [{"Name": "gitauto-repo-1-2", "State": "ENABLED"}],
        "NextToken": "tok",
    }
    mock_scheduler_client.list_schedules.side_effect = [
        first_page,
        RuntimeError("Page 2 failed"),
    ]

    result = get_enabled_schedules()

    # Decorator returns default set(), not partial results
    assert result == set()
    assert mock_scheduler_client.list_schedules.call_count == 2


def test_mixed_valid_and_invalid_schedules_on_same_page(mock_scheduler_client):
    # Verifies correct filtering when a single page has a mix of matching and non-matching entries
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-10-20", "State": "ENABLED"},
            {"Name": "gitauto-repo-10-30", "State": "DISABLED"},
            {"Name": "unrelated-schedule", "State": "ENABLED"},
            {"Name": "gitauto-repo-11-21", "State": "ENABLED"},
            {},  # completely empty schedule entry
            {"Name": "gitauto-repo-12-22", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert result == {(10, 20), (11, 21), (12, 22)}


def test_return_type_is_set(mock_scheduler_client):
    # Confirms the return type is a set, not a list or other collection
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-1-2", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    assert isinstance(result, set)


def test_tuples_contain_integers_not_strings(mock_scheduler_client):
    # Confirms that owner_id and repo_id are parsed as int, not left as str
    mock_scheduler_client.list_schedules.return_value = {
        "Schedules": [
            {"Name": "gitauto-repo-7-8", "State": "ENABLED"},
        ]
    }

    result = get_enabled_schedules()

    pair = next(iter(result))
    assert pair == (7, 8)
    assert isinstance(pair[0], int)
    assert isinstance(pair[1], int)
