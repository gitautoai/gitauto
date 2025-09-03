"""Unit tests for get_circleci_token function."""

import datetime
from unittest.mock import Mock, patch
import pytest
import requests
import json

from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token


class TestGetCircleciToken:
    """Test cases for get_circleci_token function."""

    @pytest.fixture
    def mock_supabase_with_token(self):
        """Mock supabase client with successful token response."""
        sample_token_data = {
            "id": "test-id-123",
            "owner_id": 12345,
            "token": "circleci-token-abc123",
            "created_by": "test-user",
            "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "updated_by": "test-user"
        }
        
        mock_response = Mock()
        mock_response.data = [sample_token_data]
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = mock_response
            yield mock_supabase, mock_table, sample_token_data

    @pytest.fixture
    def mock_supabase_empty_response(self):
        """Mock supabase client with empty response."""
        mock_response = Mock()
        mock_response.data = []
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = mock_response
            yield mock_supabase, mock_table

    @pytest.fixture
    def mock_supabase_none_response(self):
        """Mock supabase client with None response data."""
        mock_response = Mock()
        mock_response.data = None
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = mock_response
            yield mock_supabase, mock_table

    def test_returns_token_data_when_token_exists(self, mock_supabase_with_token):
        """Test that function returns CircleCI token data when token exists for owner."""
        # Arrange
        mock_supabase, mock_table, expected_token_data = mock_supabase_with_token
        owner_id = 12345
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result == expected_token_data
        mock_supabase.table.assert_called_once_with("circleci_tokens")
        mock_table.select.assert_called_once_with("*")
        mock_table.eq.assert_called_once_with("owner_id", owner_id)
        mock_table.limit.assert_called_once_with(1)
        mock_table.execute.assert_called_once()

    def test_returns_none_when_no_token_exists_empty_list(self, mock_supabase_empty_response):
        """Test that function returns None when no token exists (empty list response)."""
        # Arrange
        mock_supabase, mock_table = mock_supabase_empty_response
        owner_id = 99999
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result is None
        mock_supabase.table.assert_called_once_with("circleci_tokens")
        mock_table.select.assert_called_once_with("*")
        mock_table.eq.assert_called_once_with("owner_id", owner_id)
        mock_table.limit.assert_called_once_with(1)
        mock_table.execute.assert_called_once()

    def test_returns_none_when_response_data_is_none(self, mock_supabase_none_response):
        """Test that function returns None when response data is None."""
        # Arrange
        mock_supabase, mock_table = mock_supabase_none_response
        owner_id = 12345
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result is None
        mock_supabase.table.assert_called_once_with("circleci_tokens")
        mock_table.select.assert_called_once_with("*")
        mock_table.eq.assert_called_once_with("owner_id", owner_id)
        mock_table.limit.assert_called_once_with(1)
        mock_table.execute.assert_called_once()

    def test_returns_none_when_database_exception_occurs(self):
        """Test that function returns None when database operation raises exception."""
        # Arrange
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = Exception("Database connection error")
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_returns_none_when_supabase_query_fails(self):
        """Test that function returns None when Supabase query chain fails."""
        # Arrange
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.side_effect = Exception("Query execution failed")
            
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_handles_zero_owner_id(self, mock_supabase_with_token):
        """Test that function works with zero owner_id."""
        # Arrange
        mock_supabase, mock_table, expected_token_data = mock_supabase_with_token
        owner_id = 0
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result == expected_token_data
        mock_table.eq.assert_called_once_with("owner_id", 0)

    def test_handles_large_owner_id(self, mock_supabase_with_token):
        """Test that function works with very large owner_id."""
        # Arrange
        mock_supabase, mock_table, expected_token_data = mock_supabase_with_token
        owner_id = 999999999999
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result == expected_token_data
        mock_table.eq.assert_called_once_with("owner_id", owner_id)

    def test_method_chaining_works_correctly(self, mock_supabase_with_token):
        """Test that the Supabase method chaining works correctly."""
        # Arrange
        mock_supabase, mock_table, _ = mock_supabase_with_token
        owner_id = 12345
        
        # Act
        get_circleci_token(owner_id)
        
        # Assert - Verify the method chaining sequence
        assert mock_table.select.return_value == mock_table
        assert mock_table.eq.return_value == mock_table
        assert mock_table.limit.return_value == mock_table
        mock_table.execute.assert_called_once()

    def test_handle_exceptions_decorator_applied(self):
        """Test that the handle_exceptions decorator is properly applied."""
        # Arrange
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = Exception("General error")
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert - Should return None due to handle_exceptions decorator
            assert result is None
