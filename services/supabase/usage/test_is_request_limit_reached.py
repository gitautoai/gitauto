from unittest.mock import patch

from services.supabase.usage.is_request_limit_reached import is_request_limit_reached, DEFAULT


def test_is_request_limit_reached_exception_handling():
    """Test that exceptions are handled gracefully and return default value"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    owner_type = "User"
    repo_name = "test-repo"
    issue_number = 123
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer:
        mock_get_customer.side_effect = Exception("Test exception")
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
        )
    
    # Assert
    assert result == DEFAULT