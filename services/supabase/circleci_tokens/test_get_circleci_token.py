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
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_supabase.table.return_value.select.assert_called_once_with("*")
    mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("owner_id", 12345)
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.assert_called_once_with(1)
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.assert_called_once()


def test_get_circleci_token_not_found(mock_supabase):
    """Test when no CircleCI token is found for the owner."""
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


def test_get_circleci_token_none_data(mock_supabase):
    """Test when result data is None."""
    # Setup mock with None data
    mock_result = Mock()
    mock_result.data = None
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    # Execute function
    result = get_circleci_token(owner_id=54321)
    
    # Verify result
    assert result is None


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
