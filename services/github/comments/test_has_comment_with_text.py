# pylint: disable=unused-argument,too-many-instance-attributes
from unittest.mock import patch

import pytest
from faker import Faker

from config import GITHUB_APP_USER_NAME
from services.github.comments.has_comment_with_text import has_comment_with_text

fake = Faker()


@pytest.fixture
def owner():
    return fake.user_name()


@pytest.fixture
def repo():
    return fake.slug()


@pytest.fixture
def token():
    return fake.sha256()


@pytest.fixture
def mock_get_all_comments():
    with patch(
        "services.github.comments.has_comment_with_text.get_all_comments"
    ) as mock:
        yield mock


def test_has_comment_with_text_found_single_text(
    owner, repo, token, mock_get_all_comments
):
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This is a test comment with specific text",
        },
        {"user": {"login": "other_user"}, "body": "This comment should be ignored"},
    ]
    mock_get_all_comments.return_value = mock_comments

    result = has_comment_with_text(
        owner=owner,
        repo=repo,
        issue_number=fake.random_int(min=1, max=999),
        token=token,
        texts=["specific text"],
    )

    assert result is True


def test_has_comment_with_text_found_multiple_texts(
    owner, repo, token, mock_get_all_comments
):
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This comment contains the second text",
        }
    ]
    mock_get_all_comments.return_value = mock_comments

    result = has_comment_with_text(
        owner=owner,
        repo=repo,
        issue_number=fake.random_int(min=1, max=999),
        token=token,
        texts=["first text", "second text", "third text"],
    )

    assert result is True


def test_has_comment_with_text_not_found(owner, repo, token, mock_get_all_comments):
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This is a comment without the target",
        }
    ]
    mock_get_all_comments.return_value = mock_comments

    result = has_comment_with_text(
        owner=owner,
        repo=repo,
        issue_number=fake.random_int(min=1, max=999),
        token=token,
        texts=["missing text"],
    )

    assert result is False


def test_has_comment_with_text_wrong_user(owner, repo, token, mock_get_all_comments):
    mock_comments = [
        {"user": {"login": "other_user"}, "body": "This comment has the target text"}
    ]
    mock_get_all_comments.return_value = mock_comments

    result = has_comment_with_text(
        owner=owner,
        repo=repo,
        issue_number=fake.random_int(min=1, max=999),
        token=token,
        texts=["target text"],
    )

    assert result is False


def test_has_comment_with_text_empty_comments(
    owner, repo, token, mock_get_all_comments
):
    mock_get_all_comments.return_value = []

    result = has_comment_with_text(
        owner=owner,
        repo=repo,
        issue_number=fake.random_int(min=1, max=999),
        token=token,
        texts=["any text"],
    )

    assert result is False


def test_has_comment_with_text_empty_texts_list(
    owner, repo, token, mock_get_all_comments
):
    mock_comments = [
        {"user": {"login": GITHUB_APP_USER_NAME}, "body": "This is a comment"}
    ]
    mock_get_all_comments.return_value = mock_comments

    result = has_comment_with_text(
        owner=owner,
        repo=repo,
        issue_number=fake.random_int(min=1, max=999),
        token=token,
        texts=[],
    )

    assert result is False


def test_has_comment_with_text_get_all_comments_exception(
    owner, repo, token, mock_get_all_comments
):
    mock_get_all_comments.side_effect = Exception("API error")

    result = has_comment_with_text(
        owner=owner,
        repo=repo,
        issue_number=fake.random_int(min=1, max=999),
        token=token,
        texts=["any text"],
    )

    assert result is False
