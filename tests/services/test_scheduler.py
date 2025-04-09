import pytest
from unittest.mock import patch, MagicMock
from tests.constants import OWNER, REPO, INSTALLATION_ID, TOKEN
from scheduler import schedule_handler


@pytest.fixture
def mock_dependencies():
    with patch("scheduler.get_installation_ids") as mock_get_ids, \
         patch("scheduler.get_installation_access_token") as mock_get_token, \
         patch("scheduler.get_installed_owners_and_repos") as mock_get_owners, \
         patch("scheduler.get_oldest_unassigned_open_issue") as mock_get_issue, \
         patch("scheduler.get_how_many_requests_left_and_cycle") as mock_get_requests, \
         patch("scheduler.add_label_to_issue") as mock_add_label, \
         patch("scheduler.time.sleep") as mock_sleep:
        yield {
            "get_ids": mock_get_ids,
            "get_token": mock_get_token,
            "get_owners": mock_get_owners,
            "get_issue": mock_get_issue,
            "get_requests": mock_get_requests,
            "add_label": mock_add_label,
            "sleep": mock_sleep
        }


def test_schedule_handler_happy_path(mock_dependencies):
    mock_dependencies["get_ids"].return_value = [INSTALLATION_ID]
    mock_dependencies["get_token"].return_value = TOKEN
    mock_dependencies["get_owners"].return_value = [{"owner_id": 123, "owner": OWNER, "repo": REPO}]
    mock_dependencies["get_issue"].return_value = {"number": 1}
    mock_dependencies["get_requests"].return_value = (5, 10, "2025-12-31", False)
    
    result = schedule_handler({}, {})
    
    mock_dependencies["get_ids"].assert_called_once()
    mock_dependencies["get_token"].assert_called_once_with(installation_id=INSTALLATION_ID)
    mock_dependencies["get_owners"].assert_called_once_with(token=TOKEN)
    mock_dependencies["get_issue"].assert_called_once()
    mock_dependencies["get_requests"].assert_called_once()
    mock_dependencies["add_label"].assert_called_once()


def test_schedule_handler_no_installations(mock_dependencies):
    mock_dependencies["get_ids"].return_value = []
    
    result = schedule_handler({}, {})
    
    mock_dependencies["get_ids"].assert_called_once()
    mock_dependencies["get_token"].assert_not_called()
    mock_dependencies["get_owners"].assert_not_called()


def test_schedule_handler_invalid_token(mock_dependencies):
    mock_dependencies["get_ids"].return_value = [INSTALLATION_ID]
    mock_dependencies["get_token"].return_value = None
    
    result = schedule_handler({}, {})
    
    mock_dependencies["get_ids"].assert_called_once()
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_owners"].assert_not_called()


def test_schedule_handler_no_open_issues(mock_dependencies):
    mock_dependencies["get_ids"].return_value = [INSTALLATION_ID]
    mock_dependencies["get_token"].return_value = TOKEN
    mock_dependencies["get_owners"].return_value = [{"owner_id": 123, "owner": OWNER, "repo": REPO}]
    mock_dependencies["get_issue"].return_value = None
    
    result = schedule_handler({}, {})
    
    mock_dependencies["get_ids"].assert_called_once()
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_owners"].assert_called_once()
    mock_dependencies["get_issue"].assert_called_once()
    mock_dependencies["get_requests"].assert_not_called()
    mock_dependencies["add_label"].assert_not_called()


def test_schedule_handler_no_remaining_requests(mock_dependencies):
    mock_dependencies["get_ids"].return_value = [INSTALLATION_ID]
    mock_dependencies["get_token"].return_value = TOKEN
    mock_dependencies["get_owners"].return_value = [{"owner_id": 123, "owner": OWNER, "repo": REPO}]
    mock_dependencies["get_issue"].return_value = {"number": 1}
    mock_dependencies["get_requests"].return_value = (0, 10, "2025-12-31", False)
    
    result = schedule_handler({}, {})
    
    mock_dependencies["get_ids"].assert_called_once()
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_owners"].assert_called_once()
    mock_dependencies["get_issue"].assert_called_once()
    mock_dependencies["get_requests"].assert_called_once()
    mock_dependencies["add_label"].assert_not_called()


def test_schedule_handler_multiple_installations(mock_dependencies):
    mock_dependencies["get_ids"].return_value = [INSTALLATION_ID, INSTALLATION_ID + 1]
    mock_dependencies["get_token"].side_effect = [TOKEN, TOKEN]
    mock_dependencies["get_owners"].return_value = [
        {"owner_id": 123, "owner": OWNER, "repo": REPO},
        {"owner_id": 124, "owner": "other", "repo": "repo"}
    ]
    mock_dependencies["get_issue"].return_value = {"number": 1}
    mock_dependencies["get_requests"].return_value = (5, 10, "2025-12-31", False)
    
    result = schedule_handler({}, {})
    
    assert mock_dependencies["get_token"].call_count == 2
    assert mock_dependencies["get_owners"].call_count == 2
    assert mock_dependencies["get_issue"].call_count == 4
    assert mock_dependencies["get_requests"].call_count == 4
    assert mock_dependencies["add_label"].call_count == 4


def test_schedule_handler_rate_limit_sleep(mock_dependencies):
    mock_dependencies["get_ids"].return_value = [INSTALLATION_ID]
    mock_dependencies["get_token"].return_value = TOKEN
    mock_dependencies["get_owners"].return_value = [{"owner_id": 123, "owner": OWNER, "repo": REPO}]
    mock_dependencies["get_issue"].return_value = {"number": 1}
    mock_dependencies["get_requests"].return_value = (5, 10, "2025-12-31", False)
    
    result = schedule_handler({}, {})
    
    assert mock_dependencies["sleep"].call_count == 2
    mock_dependencies["sleep"].assert_called_with(1)