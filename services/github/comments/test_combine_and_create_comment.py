from datetime import datetime
from unittest.mock import patch, MagicMock

from services.github.comments.combine_and_create_comment import combine_and_create_comment
from tests.helpers.create_test_base_args import create_test_base_args


def test_combine_and_create_comment_with_limit_reached():
    """Test when request limit is reached - should override body with limit message"""
    # Arrange
    base_comment = "Click the checkbox below to generate a PR!"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    owner_type = "User"
    repo_name = "test-repo"
    issue_number = 123
    sender_name = "test-sender"
    base_args = create_test_base_args()
    
    mock_limit_result = {
        "is_limit_reached": True,
        "requests_left": 0,
        "request_limit": 10,
        "end_date": datetime(2025, 5, 1),
        "is_credit_user": False,
        "credit_balance_usd": 0,
    }
    
    # Act
    with patch("services.github.comments.combine_and_create_comment.is_request_limit_reached") as mock_limit_check, \
         patch("services.github.comments.combine_and_create_comment.create_comment") as mock_create_comment, \
         patch("services.github.comments.combine_and_create_comment.request_limit_reached") as mock_limit_message:
        
        mock_limit_check.return_value = mock_limit_result
        mock_limit_message.return_value = "Limit reached message"
        
        combine_and_create_comment(
            base_comment=base_comment,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
            sender_name=sender_name,
            base_args=base_args,
        )
    
    # Assert
    mock_limit_check.assert_called_once_with(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repo_name=repo_name,
        issue_number=issue_number,
    )
    mock_limit_message.assert_called_once_with(
        user_name=sender_name,
        request_count=10,
        end_date=datetime(2025, 5, 1),
    )
    mock_create_comment.assert_called_once_with(
        body="Limit reached message",
        base_args=base_args,
    )


def test_combine_and_create_comment_with_product_id_replacement():
    """Test when PRODUCT_ID is not 'gitauto' and body contains Generate text"""
    # Arrange
    base_comment = "Generate PR for this issue"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    owner_type = "User"
    repo_name = "test-repo"
    issue_number = 123
    sender_name = "test-sender"
    base_args = create_test_base_args()
    
    mock_limit_result = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": datetime(2025, 5, 1),
        "is_credit_user": False,
        "credit_balance_usd": 0,
    }
    
    # Act
    with patch("services.github.comments.combine_and_create_comment.is_request_limit_reached") as mock_limit_check, \
         patch("services.github.comments.combine_and_create_comment.create_comment") as mock_create_comment, \
         patch("services.github.comments.combine_and_create_comment.request_issue_comment") as mock_issue_comment, \
         patch("services.github.comments.combine_and_create_comment.PRODUCT_ID", "test-product"):
        
        mock_limit_check.return_value = mock_limit_result
        mock_issue_comment.return_value = "\n\nUsage info"
        
        combine_and_create_comment(
            base_comment=base_comment,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
            sender_name=sender_name,
            base_args=base_args,
        )
    
    # Assert
    expected_body = "Generate PR - test-product for this issue\n\nUsage info"
    mock_create_comment.assert_called_once_with(
        body=expected_body,
        base_args=base_args,
    )


def test_combine_and_create_comment_with_valid_end_date():
    """Test when end_date is valid (not default datetime) - should add usage info"""
    # Arrange
    base_comment = "Test comment"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    owner_type = "User"
    repo_name = "test-repo"
    issue_number = 123
    sender_name = "test-sender"
    base_args = create_test_base_args()
    
    mock_limit_result = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": datetime(2025, 5, 1),
        "is_credit_user": False,
        "credit_balance_usd": 0,
    }
    
    # Act
    with patch("services.github.comments.combine_and_create_comment.is_request_limit_reached") as mock_limit_check, \
         patch("services.github.comments.combine_and_create_comment.create_comment") as mock_create_comment, \
         patch("services.github.comments.combine_and_create_comment.request_issue_comment") as mock_issue_comment:
        
        mock_limit_check.return_value = mock_limit_result
        mock_issue_comment.return_value = "\n\nUsage info"
        
        combine_and_create_comment(
            base_comment=base_comment,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
            sender_name=sender_name,
            base_args=base_args,
        )
    
    # Assert
    mock_issue_comment.assert_called_once_with(
        requests_left=5,
        sender_name=sender_name,
        end_date=datetime(2025, 5, 1),
        is_credit_user=False,
        credit_balance_usd=0,
    )
    expected_body = "Test comment\n\nUsage info"
    mock_create_comment.assert_called_once_with(
        body=expected_body,
        base_args=base_args,
    )


def test_combine_and_create_comment_with_default_end_date():
    """Test when end_date is default datetime(1,1,1) - should not add usage info"""
    # Arrange
    base_comment = "Test comment"
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    owner_type = "User"
    repo_name = "test-repo"
    issue_number = 123
    sender_name = "test-sender"
    base_args = create_test_base_args()
    
    mock_limit_result = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": datetime(year=1, month=1, day=1, hour=0, minute=0, second=0),
        "is_credit_user": False,
        "credit_balance_usd": 0,
    }
    
    # Act
    with patch("services.github.comments.combine_and_create_comment.is_request_limit_reached") as mock_limit_check, \
         patch("services.github.comments.combine_and_create_comment.create_comment") as mock_create_comment, \
         patch("services.github.comments.combine_and_create_comment.request_issue_comment") as mock_issue_comment:
        
        mock_limit_check.return_value = mock_limit_result
        
        combine_and_create_comment(
            base_comment=base_comment,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
            sender_name=sender_name,
            base_args=base_args,
        )
    
    # Assert
    mock_issue_comment.assert_not_called()
    mock_create_comment.assert_called_once_with(
        body=base_comment,
        base_args=base_args,
    )


def test_combine_and_create_comment_exception_handling():
    """Test that exceptions are handled gracefully due to @handle_exceptions decorator"""
    # Arrange
    base_args = create_test_base_args()
    
    # Act
    with patch("services.github.comments.combine_and_create_comment.is_request_limit_reached") as mock_limit_check:
        mock_limit_check.side_effect = Exception("Test exception")
        
        result = combine_and_create_comment(
            base_comment="test",
            installation_id=123,
            owner_id=456,
            owner_name="test",
            owner_type="User",
            repo_name="test",
            issue_number=1,
            sender_name="test",
            base_args=base_args,
        )
    
    # Assert
    assert result is None  # Should return None due to exception handling
