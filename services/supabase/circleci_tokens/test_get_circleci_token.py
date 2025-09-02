"""Unit tests for get_circleci_token function."""

import datetime
from unittest.mock import Mock, patch
import pytest

from schemas.supabase.types import CircleciTokens
from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token


@pytest.fixture
def mock_supabase():
    """Mock supabase client with proper lifecycle management."""
    with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock:
        yield mock


@pytest.fixture
def sample_circleci_token_data():
    """Sample CircleCI token data for testing."""
    return {
        "id": "test-id-123",
        "owner_id": 12345,
        "token": "circleci-token-abc123",
        "created_by": "test-user",
        "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
        "updated_by": "test-user"
    }


class TestGetCircleciToken:
    """Test cases for get_circleci_token function."""

    def test_returns_token_data_when_token_exists(self, mock_supabase, sample_circleci_token_data):
        """Test that function returns CircleCI token data when token exists for owner."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [sample_circleci_token_data]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
        
        owner_id = 12345
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result == sample_circleci_token_data
        mock_supabase.table.assert_called_once_with("circleci_tokens")
        mock_supabase.table.return_value.select.assert_called_once_with("*")
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("owner_id", owner_id)
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.assert_called_once_with(1)

    def test_returns_none_when_no_token_exists(self, mock_supabase):
        """Test that function returns None when no token exists for owner."""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
        
        owner_id = 99999
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result is None
        mock_supabase.table.assert_called_once_with("circleci_tokens")
        mock_supabase.table.return_value.select.assert_called_once_with("*")
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("owner_id", owner_id)
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.assert_called_once_with(1)

    def test_returns_none_when_response_data_is_none(self, mock_supabase):
        """Test that function returns None when response data is None."""
        # Arrange
        mock_response = Mock()
        mock_response.data = None
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
        
        owner_id = 12345
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result is None

    def test_returns_none_when_database_exception_occurs(self, mock_supabase):
        """Test that function returns None when database operation raises exception."""
        # Arrange
        mock_supabase.table.side_effect = Exception("Database connection error")
        
        owner_id = 12345
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result is None

    def test_returns_none_when_supabase_query_fails(self, mock_supabase):
        """Test that function returns None when Supabase query chain fails."""
        # Arrange
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception("Query execution failed")
        
        owner_id = 12345
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result is None

    def test_handles_different_owner_id_types(self, mock_supabase, sample_circleci_token_data):
        """Test that function works with different valid owner_id values."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [sample_circleci_token_data]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
        
        test_owner_ids = [1, 999999, 12345]
        
        for owner_id in test_owner_ids:
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result == sample_circleci_token_data
            
        # Verify the function was called for each owner_id
        assert mock_supabase.table.call_count == len(test_owner_ids)
