# pylint: disable=unused-argument,too-many-instance-attributes
from typing import cast
from unittest.mock import patch

import pytest
from faker import Faker

from services.github.comments.create_gitauto_button_comment import (
    create_gitauto_button_comment,
)
from services.github.types.github_types import GitHubLabeledPayload

fake = Faker()


@pytest.fixture
def mock_github_labeled_payload():
    return cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "installation": {"id": fake.random_int(min=1000, max=99999)},
            "repository": {
                "owner": {
                    "id": fake.random_int(min=1000, max=99999),
                    "login": fake.user_name(),
                },
                "name": fake.slug(),
            },
            "issue": {"number": fake.random_int(min=1, max=999)},
            "sender": {
                "id": fake.random_int(min=1000, max=99999),
                "login": fake.user_name(),
            },
            "label": {"name": "gitauto"},
            "organization": {
                "id": fake.random_int(min=1000, max=99999),
                "login": fake.slug(),
            },
        },
    )


@pytest.fixture
def mock_dependencies():
    with patch(
        "services.github.comments.create_gitauto_button_comment.get_installation_access_token"
    ) as mock_get_token, patch(
        "services.github.comments.create_gitauto_button_comment.get_user_public_email"
    ) as mock_get_email, patch(
        "services.github.comments.create_gitauto_button_comment.upsert_user"
    ) as mock_upsert_user, patch(
        "services.github.comments.create_gitauto_button_comment.combine_and_create_comment"
    ) as mock_combine_comment:
        mock_get_token.return_value = fake.sha256()
        mock_get_email.return_value = fake.email()

        yield {
            "get_token": mock_get_token,
            "get_email": mock_get_email,
            "upsert_user": mock_upsert_user,
            "combine_comment": mock_combine_comment,
        }


def test_create_gitauto_button_comment_success(
    mock_github_labeled_payload, mock_dependencies
):
    result = create_gitauto_button_comment(mock_github_labeled_payload)

    assert result is None
    installation_id = mock_github_labeled_payload["installation"]["id"]
    mock_dependencies["get_token"].assert_called_once_with(
        installation_id=installation_id
    )
    mock_dependencies["combine_comment"].assert_called_once()
    call_args = mock_dependencies["combine_comment"].call_args
    assert (
        "Click the checkbox below to generate a PR!" in call_args.kwargs["base_comment"]
    )
    assert "- [ ] Generate PR" in call_args.kwargs["base_comment"]


def test_create_gitauto_button_comment_with_null_email(
    mock_github_labeled_payload, mock_dependencies
):
    mock_dependencies["get_email"].return_value = None

    result = create_gitauto_button_comment(mock_github_labeled_payload)

    assert result is None
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["combine_comment"].assert_called_once()


def test_create_gitauto_button_comment_token_error(
    mock_github_labeled_payload, mock_dependencies
):
    installation_id = mock_github_labeled_payload["installation"]["id"]
    mock_dependencies["get_token"].side_effect = ValueError(
        f"Installation {installation_id} suspended or deleted"
    )

    result = create_gitauto_button_comment(mock_github_labeled_payload)

    assert result is None
    mock_dependencies["get_token"].assert_called_once_with(
        installation_id=installation_id
    )
    mock_dependencies["get_email"].assert_not_called()
    mock_dependencies["upsert_user"].assert_not_called()
    mock_dependencies["combine_comment"].assert_not_called()


def test_create_gitauto_button_comment_email_error(
    mock_github_labeled_payload, mock_dependencies
):
    mock_dependencies["get_email"].side_effect = Exception("Email error")

    result = create_gitauto_button_comment(mock_github_labeled_payload)

    assert result is None
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_email"].assert_called_once()
    mock_dependencies["upsert_user"].assert_not_called()
    mock_dependencies["combine_comment"].assert_not_called()


def test_create_gitauto_button_comment_upsert_user_error(
    mock_github_labeled_payload, mock_dependencies
):
    mock_dependencies["upsert_user"].side_effect = Exception("Upsert error")

    result = create_gitauto_button_comment(mock_github_labeled_payload)

    assert result is None
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_email"].assert_called_once()
    mock_dependencies["upsert_user"].assert_called_once()
    mock_dependencies["combine_comment"].assert_not_called()


def test_create_gitauto_button_comment_combine_comment_error(
    mock_github_labeled_payload, mock_dependencies
):
    mock_dependencies["combine_comment"].side_effect = Exception("Comment error")

    result = create_gitauto_button_comment(mock_github_labeled_payload)

    assert result is None
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_email"].assert_called_once()
    mock_dependencies["upsert_user"].assert_called_once()
    mock_dependencies["combine_comment"].assert_called_once()
