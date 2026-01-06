# pylint: disable=unused-argument,too-many-instance-attributes
from datetime import datetime
from unittest.mock import patch

import pytest
from faker import Faker

from services.github.comments.combine_and_create_comment import (
    combine_and_create_comment,
)

fake = Faker()


@pytest.fixture
def mock_availability_status():
    return {
        "can_proceed": True,
        "user_message": "",
        "requests_left": 10,
        "billing_type": "subscription",
        "credit_balance_usd": 0,
        "period_end_date": datetime(2024, 12, 31, 23, 59, 59),
    }


@pytest.fixture
def mock_check_availability(mock_availability_status):
    with patch(
        "services.github.comments.combine_and_create_comment.check_availability"
    ) as mock:
        mock.return_value = mock_availability_status
        yield mock


@pytest.fixture
def mock_create_comment():
    with patch(
        "services.github.comments.combine_and_create_comment.create_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_request_issue_comment():
    with patch(
        "services.github.comments.combine_and_create_comment.request_issue_comment"
    ) as mock:
        mock.return_value = "\n\n@test-sender, You have 10 requests left."
        yield mock


@pytest.fixture
def mock_product_id():
    with patch(
        "services.github.comments.combine_and_create_comment.PRODUCT_ID", "gitauto"
    ):
        yield


def test_combine_and_create_comment_success_subscription_user(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
):
    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    repo_name = fake.slug()
    installation_id = fake.random_int(min=1000, max=99999)
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()
    sender_name = fake.user_name()
    base_comment = "Test comment body"

    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
        token=token,
        sender_name=sender_name,
    )

    mock_check_availability.assert_called_once_with(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        installation_id=installation_id,
        sender_name=sender_name,
    )
    expected_body = base_comment + mock_request_issue_comment.return_value
    mock_create_comment.assert_called_once_with(
        owner=owner_name,
        repo=repo_name,
        token=token,
        issue_number=issue_number,
        body=expected_body,
    )


def test_combine_and_create_comment_credit_user(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    mock_availability_status,
):
    mock_availability_status.update(
        {
            "billing_type": "credit",
            "credit_balance_usd": 50,
            "requests_left": None,
        }
    )
    mock_request_issue_comment.return_value = "\n\n@test-sender, You have $50 credits."

    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    repo_name = fake.slug()
    installation_id = fake.random_int(min=1000, max=99999)
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()
    sender_name = fake.user_name()
    base_comment = "Test comment body"

    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
        token=token,
        sender_name=sender_name,
    )

    mock_request_issue_comment.assert_called_once_with(
        requests_left=0,
        sender_name=sender_name,
        end_date=datetime(2024, 12, 31, 23, 59, 59),
        is_credit_user=True,
        credit_balance_usd=50,
    )


def test_combine_and_create_comment_no_period_end_date(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    mock_availability_status,
):
    mock_availability_status["period_end_date"] = None

    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    repo_name = fake.slug()
    installation_id = fake.random_int(min=1000, max=99999)
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()
    sender_name = fake.user_name()
    base_comment = "Test comment body"

    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
        token=token,
        sender_name=sender_name,
    )

    mock_request_issue_comment.assert_not_called()
    mock_create_comment.assert_called_once_with(
        owner=owner_name,
        repo=repo_name,
        token=token,
        issue_number=issue_number,
        body=base_comment,
    )


def test_combine_and_create_comment_default_end_date(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    mock_availability_status,
):
    mock_availability_status["period_end_date"] = datetime(
        year=1, month=1, day=1, hour=0, minute=0, second=0
    )

    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    repo_name = fake.slug()
    installation_id = fake.random_int(min=1000, max=99999)
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()
    sender_name = fake.user_name()
    base_comment = "Test comment body"

    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
        token=token,
        sender_name=sender_name,
    )

    mock_request_issue_comment.assert_not_called()
    mock_create_comment.assert_called_once_with(
        owner=owner_name,
        repo=repo_name,
        token=token,
        issue_number=issue_number,
        body=base_comment,
    )


def test_combine_and_create_comment_cannot_proceed_with_user_message(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    mock_availability_status,
):
    mock_availability_status.update(
        {
            "can_proceed": False,
            "user_message": "You have reached your request limit.",
        }
    )

    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    repo_name = fake.slug()
    installation_id = fake.random_int(min=1000, max=99999)
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()
    sender_name = fake.user_name()
    base_comment = "Test comment body"

    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
        token=token,
        sender_name=sender_name,
    )

    mock_create_comment.assert_called_once_with(
        owner=owner_name,
        repo=repo_name,
        token=token,
        issue_number=issue_number,
        body="You have reached your request limit.",
    )


def test_combine_and_create_comment_cannot_proceed_no_user_message(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    mock_availability_status,
):
    mock_availability_status.update(
        {
            "can_proceed": False,
            "user_message": "",
        }
    )

    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    repo_name = fake.slug()
    installation_id = fake.random_int(min=1000, max=99999)
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()
    sender_name = fake.user_name()
    base_comment = "Test comment body"

    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
        token=token,
        sender_name=sender_name,
    )

    expected_body = base_comment + mock_request_issue_comment.return_value
    mock_create_comment.assert_called_once_with(
        owner=owner_name,
        repo=repo_name,
        token=token,
        issue_number=issue_number,
        body=expected_body,
    )


def test_combine_and_create_comment_product_id_replacement(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
):
    with patch(
        "services.github.comments.combine_and_create_comment.PRODUCT_ID",
        "custom-product",
    ):
        owner_id = fake.random_int(min=1000, max=99999)
        owner_name = fake.user_name()
        repo_name = fake.slug()
        installation_id = fake.random_int(min=1000, max=99999)
        issue_number = fake.random_int(min=1, max=999)
        token = fake.sha256()
        sender_name = fake.user_name()
        base_comment = "Generate Tests for this issue. Generate PR when ready."

        combine_and_create_comment(
            base_comment=base_comment,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            repo_name=repo_name,
            issue_number=issue_number,
            token=token,
            sender_name=sender_name,
        )

        expected_body = (
            "Generate Tests - custom-product for this issue. "
            "Generate PR - custom-product when ready."
            + mock_request_issue_comment.return_value
        )
        mock_create_comment.assert_called_once_with(
            owner=owner_name,
            repo=repo_name,
            token=token,
            issue_number=issue_number,
            body=expected_body,
        )


def test_combine_and_create_comment_no_product_id_replacement_for_gitauto(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
):
    owner_id = fake.random_int(min=1000, max=99999)
    owner_name = fake.user_name()
    repo_name = fake.slug()
    installation_id = fake.random_int(min=1000, max=99999)
    issue_number = fake.random_int(min=1, max=999)
    token = fake.sha256()
    sender_name = fake.user_name()
    base_comment = "Generate Tests for this issue. Generate PR when ready."

    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
        token=token,
        sender_name=sender_name,
    )

    expected_body = base_comment + mock_request_issue_comment.return_value
    mock_create_comment.assert_called_once_with(
        owner=owner_name,
        repo=repo_name,
        token=token,
        issue_number=issue_number,
        body=expected_body,
    )


def test_combine_and_create_comment_exception_handling(mock_create_comment):
    with patch(
        "services.github.comments.combine_and_create_comment.check_availability"
    ) as mock_check:
        mock_check.side_effect = Exception("API error")

        owner_id = fake.random_int(min=1000, max=99999)
        owner_name = fake.user_name()
        repo_name = fake.slug()
        installation_id = fake.random_int(min=1000, max=99999)
        issue_number = fake.random_int(min=1, max=999)
        token = fake.sha256()
        sender_name = fake.user_name()

        result = combine_and_create_comment(
            base_comment="Test",
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            repo_name=repo_name,
            issue_number=issue_number,
            token=token,
            sender_name=sender_name,
        )

        assert result is None
        mock_create_comment.assert_not_called()
