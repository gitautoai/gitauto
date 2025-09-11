from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from services.github.comments.combine_and_create_comment import combine_and_create_comment


@pytest.fixture
def mock_availability_status():
    """Default availability status for testing."""
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
    """Mock check_availability function."""
    with patch(
        "services.github.comments.combine_and_create_comment.check_availability"
    ) as mock:
        mock.return_value = mock_availability_status
        yield mock


@pytest.fixture
def mock_create_comment():
    """Mock create_comment function."""
    with patch(
        "services.github.comments.combine_and_create_comment.create_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_request_issue_comment():
    """Mock request_issue_comment function."""
    with patch(
        "services.github.comments.combine_and_create_comment.request_issue_comment"
    ) as mock:
        mock.return_value = "\n\n@test-sender, You have 10 requests left in this cycle which refreshes on 2024-12-31 23:59:59.\nIf you have any questions or concerns, please contact us at info@gitauto.ai."
        yield mock


@pytest.fixture
def mock_product_id():
    """Mock PRODUCT_ID constant."""
    with patch("services.github.comments.combine_and_create_comment.PRODUCT_ID", "gitauto"):
        yield


def test_combine_and_create_comment_success_subscription_user(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    create_test_base_args,
):
    """Test successful comment creation for subscription user."""
    # Arrange
    base_comment = "Test comment body"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    sender_name = "test-sender"
    base_args = create_test_base_args(repo="test-repo")

    # Act
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        sender_name=sender_name,
        base_args=base_args,
    )

    # Assert
    mock_check_availability.assert_called_once_with(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name="test-repo",
        installation_id=installation_id,
        sender_name=sender_name,
    )
    mock_request_issue_comment.assert_called_once_with(
        requests_left=10,
        sender_name=sender_name,
        end_date=datetime(2024, 12, 31, 23, 59, 59),
        is_credit_user=False,
        credit_balance_usd=0,
    )
    expected_body = base_comment + mock_request_issue_comment.return_value
    mock_create_comment.assert_called_once_with(body=expected_body, base_args=base_args)


def test_combine_and_create_comment_credit_user(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    create_test_base_args,
    mock_availability_status,
):
    """Test comment creation for credit user."""
    # Arrange
    mock_availability_status.update({
        "billing_type": "credit",
        "credit_balance_usd": 50,
        "requests_left": None,
    })
    mock_request_issue_comment.return_value = "\n\n@test-sender, You have $50 in credits remaining. [View credits](https://dashboard.gitauto.ai/credits)\nIf you have any questions or concerns, please contact us at info@gitauto.ai."
    
    base_comment = "Test comment body"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    sender_name = "test-sender"
    base_args = create_test_base_args(repo="test-repo")

    # Act
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        sender_name=sender_name,
        base_args=base_args,
    )

    # Assert
    mock_request_issue_comment.assert_called_once_with(
        requests_left=0,
        sender_name=sender_name,
        end_date=datetime(2024, 12, 31, 23, 59, 59),
        is_credit_user=True,
        credit_balance_usd=50,
    )
    expected_body = base_comment + mock_request_issue_comment.return_value
    mock_create_comment.assert_called_once_with(body=expected_body, base_args=base_args)


def test_combine_and_create_comment_no_period_end_date(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    create_test_base_args,
    mock_availability_status,
):
    """Test comment creation when period_end_date is None."""
    # Arrange
    mock_availability_status["period_end_date"] = None
    
    base_comment = "Test comment body"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    sender_name = "test-sender"
    base_args = create_test_base_args(repo="test-repo")

    # Act
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        sender_name=sender_name,
        base_args=base_args,
    )

    # Assert
    mock_request_issue_comment.assert_not_called()
    mock_create_comment.assert_called_once_with(body=base_comment, base_args=base_args)


def test_combine_and_create_comment_cannot_proceed_with_user_message(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    create_test_base_args,
    mock_availability_status,
):
    """Test comment creation when user cannot proceed and has user message."""
    # Arrange
    mock_availability_status.update({
        "can_proceed": False,
        "user_message": "You have reached your request limit.",
    })
    
    base_comment = "Test comment body"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    sender_name = "test-sender"
    base_args = create_test_base_args(repo="test-repo")

    # Act
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        sender_name=sender_name,
        base_args=base_args,
    )

    # Assert
    mock_request_issue_comment.assert_not_called()
    mock_create_comment.assert_called_once_with(
        body="You have reached your request limit.", base_args=base_args
    )


def test_combine_and_create_comment_cannot_proceed_no_user_message(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    create_test_base_args,
    mock_availability_status,
):
    """Test comment creation when user cannot proceed but no user message."""
    # Arrange
    mock_availability_status.update({
        "can_proceed": False,
        "user_message": "",
    })
    
    base_comment = "Test comment body"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    sender_name = "test-sender"
    base_args = create_test_base_args(repo="test-repo")

    # Act
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        sender_name=sender_name,
        base_args=base_args,
    )

    # Assert
    expected_body = base_comment + mock_request_issue_comment.return_value
    mock_create_comment.assert_called_once_with(body=expected_body, base_args=base_args)


def test_combine_and_create_comment_product_id_replacement(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    create_test_base_args,
):
    """Test product ID replacement in comment body."""
    # Arrange
    with patch("services.github.comments.combine_and_create_comment.PRODUCT_ID", "custom-product"):
        base_comment = "Generate Tests for this issue. Generate PR when ready."
        installation_id = 12345
        owner_id = 67890
        owner_name = "test-owner"
        sender_name = "test-sender"
        base_args = create_test_base_args(repo="test-repo")

        # Act
        combine_and_create_comment(
            base_comment=base_comment,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            sender_name=sender_name,
            base_args=base_args,
        )

        # Assert
        expected_body = "Generate Tests - custom-product for this issue. Generate PR - custom-product when ready." + mock_request_issue_comment.return_value
        mock_create_comment.assert_called_once_with(body=expected_body, base_args=base_args)


def test_combine_and_create_comment_no_product_id_replacement_for_gitauto(
    mock_check_availability,
    mock_create_comment,
    mock_request_issue_comment,
    mock_product_id,
    create_test_base_args,
):
    """Test no product ID replacement when PRODUCT_ID is 'gitauto'."""
    # Arrange
    base_comment = "Generate Tests for this issue. Generate PR when ready."
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    sender_name = "test-sender"
    base_args = create_test_base_args(repo="test-repo")

    # Act
    combine_and_create_comment(
        base_comment=base_comment,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        sender_name=sender_name,
        base_args=base_args,
    )

    # Assert
    expected_body = base_comment + mock_request_issue_comment.return_value
    mock_create_comment.assert_called_once_with(body=expected_body, base_args=base_args)


def test_combine_and_create_comment_exception_handling(
    mock_create_comment,
    create_test_base_args,
):
    """Test that exceptions are handled gracefully by the decorator."""
    # Arrange
    with patch(
        "services.github.comments.combine_and_create_comment.check_availability"
    ) as mock_check_availability:
        mock_check_availability.side_effect = Exception("API error")
        
        base_comment = "Test comment body"
        installation_id = 12345
        owner_id = 67890
        owner_name = "test-owner"
        sender_name = "test-sender"
        base_args = create_test_base_args(repo="test-repo")

        # Act
        result = combine_and_create_comment(
            base_comment=base_comment,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            sender_name=sender_name,
            base_args=base_args,
        )

        # Assert
        assert result is None  # The handle_exceptions decorator should return None on error
        mock_create_comment.assert_not_called()