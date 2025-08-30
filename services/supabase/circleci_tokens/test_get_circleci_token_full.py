"""Unit tests for get_circleci_token function."""

import datetime
from unittest.mock import Mock, patch

import pytest

from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token


@pytest.fixture
def mock_supabase():
    """Fixture to mock the supabase client."""
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock:
        yield mock


@pytest.fixture
def sample_circleci_token_data():
    """Fixture providing sample CircleCI token data."""
    return {
        "id": "test-id-123",
        "owner_id": 12345,
        "token": "circleci-token-abc123",
        "created_by": "test-user",
        "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime.datetime(2024, 1, 2, 12, 0, 0),
        "updated_by": "test-user"
    }


def test_get_circleci_token_success(mock_supabase, sample_circleci_token_data):
    """Test successful retrieval of CircleCI token."""
    # Setup mock chain
    mock_result = Mock()
    mock_result.data = [sample_circleci_token_data]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    # Execute function
    result = get_circleci_token(owner_id=12345)
    
    # Verify result
    assert result == sample_circleci_token_data
    assert isinstance(result, dict)
    assert result["owner_id"] == 12345
    assert result["token"] == "circleci-token-abc123"
    assert result["id"] == "test-id-123"
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_supabase.table.return_value.select.assert_called_once_with("*")
    mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("owner_id", 12345)
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.assert_called_once_with(1)
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.assert_called_once()


def test_get_circleci_token_not_found_empty_data(mock_supabase):
    """Test when no CircleCI token is found for the owner (empty data list)."""
    # Setup mock with empty result
    mock_result = Mock()
    mock_result.data = []
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    # Execute function
    result = get_circleci_token(owner_id=99999)
    
    # Verify result
    assert result is None
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_supabase.table.return_value.select.assert_called_once_with("*")
    mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("owner_id", 99999)


def test_get_circleci_token_not_found_none_data(mock_supabase):
    """Test when result data is None."""
    # Setup mock with None data
    mock_result = Mock()
    mock_result.data = None
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    # Execute function
    result = get_circleci_token(owner_id=54321)
    
    # Verify result
    assert result is None
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("circleci_tokens")


def test_get_circleci_token_first_item_none(mock_supabase):
    """Test when first item in data is None."""
    mock_result = Mock()
    mock_result.data = [None]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    result = get_circleci_token(owner_id=12345)
    
    # Should return None when first item is None
    assert result is None
    mock_supabase.table.assert_called_once_with("circleci_tokens")


def test_get_circleci_token_first_item_empty_dict(mock_supabase):
    """Test when first item in data is empty dict."""
    mock_result = Mock()
    mock_result.data = [{}]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    result = get_circleci_token(owner_id=12345)
    
    # Should return the empty dict (it's still valid data)
    assert result == {}
    mock_supabase.table.assert_called_once_with("circleci_tokens")


def test_get_circleci_token_multiple_results(mock_supabase, sample_circleci_token_data):
    """Test when multiple results are returned (should return first one due to limit(1))."""
    # Setup mock with multiple results
    second_token_data = sample_circleci_token_data.copy()
    second_token_data["id"] = "test-id-456"
    second_token_data["token"] = "circleci-token-def456"
    
    mock_result = Mock()
    mock_result.data = [sample_circleci_token_data, second_token_data]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    # Execute function
    result = get_circleci_token(owner_id=12345)
    
    # Verify result (should return first item)
    assert result == sample_circleci_token_data
    assert result["id"] == "test-id-123"
    assert result["token"] == "circleci-token-abc123"


def test_get_circleci_token_exception_handling(mock_supabase):
    """Test exception handling with @handle_exceptions decorator."""
    # Setup mock to raise exception
    mock_supabase.table.side_effect = Exception("Database connection error")
    
    # Execute function
    result = get_circleci_token(owner_id=12345)
    
    # Verify result (should return None due to @handle_exceptions)
    assert result is None
    
    # Verify supabase was called
    mock_supabase.table.assert_called_once_with("circleci_tokens")


def test_get_circleci_token_attribute_error(mock_supabase):
    """Test handling AttributeError and returns None."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = AttributeError(
        "'NoneType' object has no attribute 'execute'"
    )
    
    result = get_circleci_token(owner_id=12345)
    
    assert result is None


def test_get_circleci_token_key_error(mock_supabase):
    """Test handling KeyError and returns None."""
    mock_result = Mock()
    # Simulate a result object that doesn't have expected attributes
    del mock_result.data
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    result = get_circleci_token(owner_id=12345)
    
    assert result is None


def test_get_circleci_token_type_error(mock_supabase):
    """Test handling TypeError and returns None."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = TypeError(
        "unsupported operand type(s)"
    )
    
    result = get_circleci_token(owner_id=12345)
    
    assert result is None


def test_get_circleci_token_with_different_owner_ids():
    """Test get_circleci_token works with different owner_id values."""
    test_cases = [
        (1, "token-1"),
        (999999999, "large-owner-token"),
        (0, "zero-owner-token"),
    ]
    
    for owner_id, token in test_cases:
        mock_result = Mock()
        mock_result.data = [
            {
                "id": f"test-id-{owner_id}",
                "owner_id": owner_id,
                "token": token,
                "created_by": "test-user",
                "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
                "updated_at": datetime.datetime(2024, 1, 2, 12, 0, 0),
                "updated_by": "test-user"
            }
        ]
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
            
            result = get_circleci_token(owner_id)
            
            assert result is not None
            assert result["owner_id"] == owner_id
            assert result["token"] == token
            mock_supabase.table.return_value.select.return_value.eq.assert_called_with("owner_id", owner_id)


def test_get_circleci_token_with_negative_owner_id():
    """Test get_circleci_token works with negative owner_id (edge case)."""
    # This tests that the function doesn't validate input and passes it through
    mock_result = Mock()
    mock_result.data = []
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
        
        result = get_circleci_token(-1)
        
        assert result is None
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("owner_id", -1)


def test_get_circleci_token_supabase_chain_calls():
    """Test that the Supabase method chain is called correctly."""
    mock_result = Mock()
    mock_result.data = [{"owner_id": 12345, "token": "test-token"}]
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        # Set up the method chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_limit = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_result
        
        result = get_circleci_token(12345)
        
        # Verify each step of the chain
        mock_supabase.table.assert_called_once_with("circleci_tokens")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("owner_id", 12345)
        mock_eq.limit.assert_called_once_with(1)
        mock_limit.execute.assert_called_once()
        
        assert result is not None
        assert result["owner_id"] == 12345


def test_get_circleci_token_data_with_false_values():
    """Test get_circleci_token handles data with falsy values correctly."""
    mock_result = Mock()
    mock_result.data = [
        {
            "id": "",  # Empty string is falsy but valid
            "owner_id": 0,  # Zero is falsy but valid
            "token": "",  # Empty token is falsy but valid
            "created_by": "",
            "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2024, 1, 2, 12, 0, 0),
            "updated_by": ""
        }
    ]
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
        
        result = get_circleci_token(0)
        
        # Should return the data even with falsy values
        assert result is not None
        assert result["id"] == ""
        assert result["owner_id"] == 0
        assert result["token"] == ""
        assert result["created_by"] == ""


def test_get_circleci_token_minimal_valid_data():
    """Test get_circleci_token with minimal valid token data."""
    mock_result = Mock()
    mock_result.data = [{"owner_id": 12345}]  # Minimal data
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
        
        result = get_circleci_token(12345)
        
        assert result is not None
        assert result["owner_id"] == 12345
        assert len(result) == 1  # Only one field


def test_get_circleci_token_decorator_various_exceptions():
    """Test that the handle_exceptions decorator returns None on various exception types."""
    # Test various exception types to ensure decorator handles them all
    exception_types = [
        ValueError("Invalid value"),
        RuntimeError("Runtime error"),
        ConnectionError("Connection failed"),
        TimeoutError("Request timed out"),
    ]
    
    for exception in exception_types:
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = exception
            
            result = get_circleci_token(12345)
            
            # Decorator should catch all exceptions and return None
            assert result is None


def test_get_circleci_token_decorator_raise_on_error_false():
    """Test that the decorator doesn't raise exceptions when raise_on_error=False."""
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Critical error")
        
        # Should not raise an exception due to decorator configuration
        result = get_circleci_token(12345)
        assert result is None


def test_get_circleci_token_data_index_out_of_bounds():
    """Test get_circleci_token handles empty data list gracefully."""
    mock_result = Mock()
    mock_result.data = []
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
        
        result = get_circleci_token(12345)
        
        # Should return None when trying to access data[0] on empty list
        assert result is None


def test_get_circleci_token_cast_behavior(sample_circleci_token_data):
    """Test that the result is properly cast to CircleciTokens type."""
    mock_result = Mock()
    mock_result.data = [sample_circleci_token_data]
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
        
        result = get_circleci_token(12345)
        
        # The cast function should return the dictionary as-is
        assert result is not None
        assert isinstance(result, dict)
        assert result == sample_circleci_token_data


def test_get_circleci_token_return_types():
    """Test that get_circleci_token returns correct types."""
    # Test successful case
    mock_result = Mock()
    mock_result.data = [{"owner_id": 12345, "token": "test-token"}]
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
        
        result = get_circleci_token(12345)
        
        assert isinstance(result, dict)
        assert result is not None
    
    # Test not found case
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    result = get_circleci_token(99999)
    
    assert result is None
    assert not isinstance(result, dict)


def test_get_circleci_token_complete_circleci_tokens_structure(sample_circleci_token_data):
    """Test get_circleci_token with complete CircleciTokens structure."""
    mock_result = Mock()
    mock_result.data = [sample_circleci_token_data]
    
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
        
        result = get_circleci_token(12345)
        
        # Verify all expected fields are present
        assert result is not None
        assert "id" in result
        assert "owner_id" in result
        assert "token" in result
        assert "created_by" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "updated_by" in result
        
        # Verify field types
        assert isinstance(result["id"], str)
        assert isinstance(result["owner_id"], int)
        assert isinstance(result["token"], str)
        assert isinstance(result["created_by"], str)
        assert isinstance(result["created_at"], datetime.datetime)
        assert isinstance(result["updated_at"], datetime.datetime)
        assert isinstance(result["updated_by"], str)