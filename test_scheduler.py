import pytest
from unittest.mock import patch, MagicMock
from tests.constants import OWNER, REPO, INSTALLATION_ID, TOKEN
from scheduler import schedule_handler
from config import PRODUCT_ID


@pytest.fixture
def mock_get_installation_ids():
    with patch("scheduler.get_installation_ids") as mock:
        mock.return_value = [INSTALLATION_ID]
        yield mock


@pytest.fixture
def mock_get_installation_access_token():
    with patch("scheduler.get_installation_access_token") as mock:
        mock.return_value = TOKEN
        yield mock


@pytest.fixture
def mock_get_installed_owners_and_repos():
    with patch("scheduler.get_installed_owners_and_repos") as mock:
        mock.return_value = [{"owner_id": 123, "owner": OWNER, "repo": REPO}]
        yield mock


@pytest.fixture
def mock_get_oldest_unassigned_open_issue():
    with patch("scheduler.get_oldest_unassigned_open_issue") as mock:
        mock.return_value = {"number": 1}
        yield mock


@pytest.fixture
def mock_get_how_many_requests_left_and_cycle():
    with patch("scheduler.get_how_many_requests_left_and_cycle") as mock:
        mock.return_value = (5, 10, "2025-12-31", False)
        yield mock


@pytest.fixture
def mock_add_label_to_issue():
    with patch("scheduler.add_label_to_issue") as mock:
        mock.return_value = None
        yield mock


def test_schedule_handler_happy_path(
    mock_get_installation_ids,
    mock_get_installation_access_token,
    mock_get_installed_owners_and_repos,
    mock_get_oldest_unassigned_open_issue,
    mock_get_how_many_requests_left_and_cycle,
    mock_add_label_to_issue,
):
    result = schedule_handler({}, {})
    mock_get_installation_ids.assert_called_once()
    mock_get_installation_access_token.assert_called_once_with(installation_id=INSTALLATION_ID)
    mock_get_installed_owners_and_repos.assert_called_once_with(token=TOKEN)
    mock_get_oldest_unassigned_open_issue.assert_called_once_with(owner=OWNER, repo=REPO, token=TOKEN)
    mock_get_how_many_requests_left_and_cycle.assert_called_once()
    mock_add_label_to_issue.assert_called_once_with(
        owner=OWNER, repo=REPO, issue_number=1, label=PRODUCT_ID, token=TOKEN
    )


def test_schedule_handler_no_token(
    mock_get_installation_ids,
    mock_get_installation_access_token,
):
    mock_get_installation_access_token.return_value = None
    result = schedule_handler({}, {})
    mock_get_installation_ids.assert_called_once()
    mock_get_installation_access_token.assert_called_once_with(installation_id=INSTALLATION_ID)


def test_schedule_handler_no_open_issue(
    mock_get_installation_ids,
    mock_get_installation_access_token,
    mock_get_installed_owners_and_repos,
    mock_get_oldest_unassigned_open_issue,
):
    mock_get_oldest_unassigned_open_issue.return_value = None
    result = schedule_handler({}, {})
    mock_get_installation_ids.assert_called_once()
    mock_get_installation_access_token.assert_called_once_with(installation_id=INSTALLATION_ID)
    mock_get_installed_owners_and_repos.assert_called_once_with(token=TOKEN)
    mock_get_oldest_unassigned_open_issue.assert_called_once_with(owner=OWNER, repo=REPO, token=TOKEN)


def test_schedule_handler_no_requests_left(
    mock_get_installation_ids,
    mock_get_installation_access_token,
    mock_get_installed_owners_and_repos,
    mock_get_oldest_unassigned_open_issue,
    mock_get_how_many_requests_left_and_cycle,
):
    mock_get_how_many_requests_left_and_cycle.return_value = (0, 10, "2025-12-31", False)
    result = schedule_handler({}, {})
    mock_get_installation_ids.assert_called_once()
    mock_get_installation_access_token.assert_called_once_with(installation_id=INSTALLATION_ID)
    mock_get_installed_owners_and_repos.assert_called_once_with(token=TOKEN)
    mock_get_oldest_unassigned_open_issue.assert_called_once_with(owner=OWNER, repo=REPO, token=TOKEN)
    mock_get_how_many_requests_left_and_cycle.assert_called_once()