# pylint: disable=unused-argument,too-many-instance-attributes
import inspect
from unittest.mock import patch

import pytest
from faker import Faker

from services.github.comments.delete_comments_by_identifiers import (
    delete_comments_by_identifiers,
)

fake = Faker()


@pytest.fixture
def mock_get_all_comments():
    with patch(
        "services.github.comments.delete_comments_by_identifiers.get_all_comments"
    ) as mock:
        yield mock


@pytest.fixture
def mock_filter_comments_by_identifiers():
    with patch(
        "services.github.comments.delete_comments_by_identifiers.filter_comments_by_identifiers"
    ) as mock:
        yield mock


@pytest.fixture
def mock_delete_comment():
    with patch(
        "services.github.comments.delete_comments_by_identifiers.delete_comment"
    ) as mock:
        yield mock


def test_delete_comments_by_identifiers_successful_deletion(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
):
    owner = fake.user_name()
    repo = fake.slug()
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()

    sample_comments = [
        {"id": 1, "body": "Comment with id-1", "user": {"login": "gitauto-ai[bot]"}},
        {"id": 2, "body": "Comment with id-2", "user": {"login": "gitauto-ai[bot]"}},
    ]
    mock_get_all_comments.return_value = sample_comments
    mock_filter_comments_by_identifiers.return_value = sample_comments
    mock_delete_comment.return_value = None

    identifiers = ["id-1", "id-2"]

    result = delete_comments_by_identifiers(
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        token=token,
        identifiers=identifiers,
    )

    assert result is None
    mock_get_all_comments.assert_called_once_with(
        owner=owner, repo=repo, issue_number=issue_number, token=token
    )
    assert mock_delete_comment.call_count == 2


def test_delete_comments_by_identifiers_no_comments_found(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
):
    owner = fake.user_name()
    repo = fake.slug()
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()

    mock_get_all_comments.return_value = []
    mock_filter_comments_by_identifiers.return_value = []

    result = delete_comments_by_identifiers(
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        token=token,
        identifiers=["test-identifier"],
    )

    assert result is None
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_no_matching_comments(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
):
    owner = fake.user_name()
    repo = fake.slug()
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()

    sample_comments = [
        {"id": 1, "body": "Some comment", "user": {"login": "gitauto-ai[bot]"}}
    ]
    mock_get_all_comments.return_value = sample_comments
    mock_filter_comments_by_identifiers.return_value = []

    result = delete_comments_by_identifiers(
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        token=token,
        identifiers=["non-existent"],
    )

    assert result is None
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_exception_handling(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
):
    owner = fake.user_name()
    repo = fake.slug()
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()

    mock_get_all_comments.side_effect = Exception("API error")

    result = delete_comments_by_identifiers(
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        token=token,
        identifiers=["test-identifier"],
    )

    assert result is None
    mock_filter_comments_by_identifiers.assert_not_called()
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_delete_comment_exception(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
):
    owner = fake.user_name()
    repo = fake.slug()
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()

    matching_comments = [
        {"id": 1, "body": "test", "user": {"login": "gitauto-ai[bot]"}}
    ]
    mock_get_all_comments.return_value = matching_comments
    mock_filter_comments_by_identifiers.return_value = matching_comments
    mock_delete_comment.side_effect = Exception("Delete failed")

    result = delete_comments_by_identifiers(
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        token=token,
        identifiers=["test-identifier"],
    )

    assert result is None
    mock_delete_comment.assert_called_once()


def test_delete_comments_by_identifiers_function_signature():
    sig = inspect.signature(delete_comments_by_identifiers)
    params = sig.parameters

    assert "owner" in params
    assert "repo" in params
    assert "issue_number" in params
    assert "token" in params
    assert "identifiers" in params
    assert len(params) == 5


def test_delete_comments_by_identifiers_decorator_applied():
    assert hasattr(delete_comments_by_identifiers, "__wrapped__")
