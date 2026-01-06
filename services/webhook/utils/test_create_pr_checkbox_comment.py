# pylint: disable=unused-argument,too-many-instance-attributes
from typing import cast
from unittest.mock import patch

import pytest
from faker import Faker

from services.github.types.pull_request_webhook_payload import PullRequestWebhookPayload
from services.webhook.utils.create_pr_checkbox_comment import (
    create_pr_checkbox_comment,
)
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER

fake = Faker()


@pytest.fixture
def mock_get_installation_access_token():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token"
    ) as mock:
        mock.return_value = fake.sha256()
        yield mock


@pytest.fixture
def mock_get_repository():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_repository"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_pull_request_files():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_coverages():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_coverages"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_code_file():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.is_code_file"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_test_file():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.is_test_file"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_type_file():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.is_type_file"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_file_checklist():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_file_checklist"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_test_selection_comment():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_delete_comments_by_identifiers():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers"
    ) as mock:
        yield mock


@pytest.fixture
def mock_combine_and_create_comment():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_logging():
    with patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock:
        yield mock


def create_test_payload():
    sender_name = fake.user_name()
    repo_id = fake.random_int(min=1000, max=99999)
    repo_name = fake.slug()
    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    pull_number = fake.random_int(min=1, max=999)
    installation_id = fake.random_int(min=1000, max=99999)
    branch_name = fake.slug()
    pull_url = (
        f"https://api.github.com/repos/{owner_name}/{repo_name}/pulls/{pull_number}"
    )

    return cast(
        PullRequestWebhookPayload,
        {
            "action": "opened",
            "number": pull_number,
            "sender": {"login": sender_name},
            "repository": {
                "id": repo_id,
                "name": repo_name,
                "owner": {"id": owner_id, "login": owner_name},
            },
            "pull_request": {
                "number": pull_number,
                "url": pull_url,
                "head": {"ref": branch_name},
            },
            "installation": {"id": installation_id},
        },
    )


def test_skips_bot_sender(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    payload = create_test_payload()
    payload["sender"]["login"] = "dependabot[bot]"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_repository.assert_not_called()
    mock_get_installation_access_token.assert_not_called()


def test_skips_when_repository_not_found(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    payload = create_test_payload()
    mock_get_repository.return_value = None

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_installation_access_token.assert_not_called()


def test_skips_when_trigger_on_pr_change_is_false(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": False}

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_installation_access_token.assert_not_called()


def test_skips_when_no_code_files_changed(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "test_file.py"},
        {"filename": "types.py"},
    ]
    mock_is_code_file.return_value = True
    mock_is_test_file.side_effect = lambda f: f == "test_file.py"
    mock_is_type_file.side_effect = lambda f: f == "types.py"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_coverages.assert_not_called()


def test_successful_comment_creation(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/file1.py"},
        {"filename": "src/file2.py"},
    ]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file1.py": {}, "src/file2.py": {}}
    mock_create_file_checklist.return_value = [
        {"path": "src/file1.py", "checked": True},
        {"path": "src/file2.py", "checked": True},
    ]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    owner_id = payload["repository"]["owner"]["id"]
    repo_id = payload["repository"]["id"]
    installation_id = payload["installation"]["id"]
    mock_get_repository.assert_called_once_with(owner_id=owner_id, repo_id=repo_id)
    mock_get_installation_access_token.assert_called_once_with(
        installation_id=installation_id
    )
    mock_combine_and_create_comment.assert_called_once()


def test_delete_comments_called_with_correct_identifier(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_delete_comments_by_identifiers.assert_called_once()
    call_args = mock_delete_comments_by_identifiers.call_args
    assert call_args[1]["identifiers"] == [TEST_SELECTION_COMMENT_IDENTIFIER]
