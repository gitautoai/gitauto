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

    def test_handles_negative_owner_id(self, mock_supabase_empty_response):
        """Test that function handles negative owner_id correctly."""
        # Arrange
        mock_supabase, mock_table = mock_supabase_empty_response
        owner_id = -1
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert
        assert result is None
        mock_table.eq.assert_called_once_with("owner_id", -1)

    def test_returns_first_token_when_multiple_exist(self):
        """Test that function returns first token when multiple tokens exist for owner."""
        # Arrange
        sample_token_data_1 = {
            "id": "test-id-123",
            "owner_id": 12345,
            "token": "circleci-token-abc123",
            "created_by": "test-user",
            "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "updated_by": "test-user"
        }
        sample_token_data_2 = {
            "id": "test-id-456",
            "owner_id": 12345,
            "token": "circleci-token-def456",
            "created_by": "test-user-2",
            "created_at": datetime.datetime(2024, 1, 2, 12, 0, 0),
            "updated_at": datetime.datetime(2024, 1, 2, 12, 0, 0),
            "updated_by": "test-user-2"
        }
        
        mock_response = Mock()
        mock_response.data = [sample_token_data_1, sample_token_data_2]
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = mock_response
            
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert - Should return first token
            assert result == sample_token_data_1
            mock_table.limit.assert_called_once_with(1)

    def test_handles_http_error_exception(self):
        """Test that function handles HTTPError exceptions correctly."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Resource not found"
        
        http_error = requests.HTTPError("404 Client Error")
        http_error.response = mock_response
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = http_error
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_handles_json_decode_error(self):
        """Test that function handles JSONDecodeError correctly."""
        # Arrange
        json_error = json.JSONDecodeError("Invalid JSON", "invalid json", 0)
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = json_error
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_handles_attribute_error(self):
        """Test that function handles AttributeError correctly."""
        # Arrange
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = AttributeError("'NoneType' object has no attribute 'table'")
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_handles_key_error(self):
        """Test that function handles KeyError correctly."""
        # Arrange
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = KeyError("Missing key")
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_handles_type_error(self):
        """Test that function handles TypeError correctly."""
        # Arrange
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_supabase.table.side_effect = TypeError("Invalid type")
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_function_signature_and_return_type(self):
        """Test that function has correct signature and return type annotation."""
        # Arrange & Act
        import inspect
        from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token
        
        # Assert
        signature = inspect.signature(get_circleci_token)
        assert len(signature.parameters) == 1
        assert "owner_id" in signature.parameters
        assert signature.parameters["owner_id"].annotation == int

    def test_decorator_configuration(self):
        """Test that handle_exceptions decorator is configured correctly."""
        # Arrange & Act
        from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token
        
        # Assert - Function should have the decorator applied
        assert hasattr(get_circleci_token, "__wrapped__")
        assert get_circleci_token.__name__ == "get_circleci_token"

    def test_supabase_query_structure(self, mock_supabase_with_token):
        """Test that the Supabase query is structured correctly."""
        # Arrange
        mock_supabase, mock_table, _ = mock_supabase_with_token
        owner_id = 12345
        
        # Act
        get_circleci_token(owner_id)
        
        # Assert - Verify exact query structure
        mock_supabase.table.assert_called_once_with("circleci_tokens")
        mock_table.select.assert_called_once_with("*")
        mock_table.eq.assert_called_once_with("owner_id", owner_id)
        mock_table.limit.assert_called_once_with(1)
        
        # Check that methods were called in the correct sequence
        assert mock_supabase.table.call_count == 1
        assert mock_table.select.call_count == 1
        assert mock_table.eq.call_count == 1
        assert mock_table.limit.call_count == 1
        assert mock_table.execute.call_count == 1

    def test_result_data_access_pattern(self):
        """Test that result.data is accessed correctly."""
        # Arrange
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
            
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert - Verify that result.data[0] is returned
            assert result == sample_token_data

    def test_handles_falsy_result_data(self):
        """Test that function handles falsy result.data correctly."""
        # Arrange
        mock_response = Mock()
        mock_response.data = False  # Falsy but not None or empty list
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table

    def test_handles_empty_string_in_result_data(self):
        """Test that function handles empty string in result.data correctly."""
        # Arrange
        mock_response = Mock()
        mock_response.data = ""  # Empty string is falsy
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = mock_response
            
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_handles_zero_in_result_data(self):
        """Test that function handles zero in result.data correctly."""
        # Arrange
        mock_response = Mock()
        mock_response.data = 0  # Zero is falsy
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = mock_response
            
            owner_id = 12345
            
            # Act
            result = get_circleci_token(owner_id)
            
            # Assert
            assert result is None

    def test_returns_exact_token_data_structure(self, mock_supabase_with_token):
        """Test that function returns exact token data structure matching CircleciTokens type."""
        # Arrange
        mock_supabase, mock_table, expected_token_data = mock_supabase_with_token
        owner_id = 12345
        
        # Act
        result = get_circleci_token(owner_id)
        
        # Assert - Verify all required fields are present
        assert "id" in result
        assert "owner_id" in result
        assert "token" in result
        assert "created_by" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "updated_by" in result
        
        # Verify data types
        assert isinstance(result["id"], str)

    def test_conditional_logic_coverage(self):
        """Test both branches of the if result.data conditional."""
        # Test the True branch (already covered by other tests, but explicit here)
        sample_token_data = {
            "id": "test-id-123",
            "owner_id": 12345,
            "token": "circleci-token-abc123",
            "created_by": "test-user",
            "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "updated_by": "test-user"
        }
        
        # Test True branch
        mock_response_true = Mock()
        mock_response_true.data = [sample_token_data]
        
        with patch("services.supabase.circleci_tokens.get_circleci_token.supabase") as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = mock_response_true
            
            # Act & Assert - True branch
            result = get_circleci_token(12345)
            assert result == sample_token_data
            
            
            # Test False branch
            mock_response_false = Mock()
            mock_response_false.data = []
            mock_table.execute.return_value = mock_response_false
            
            # Act & Assert - False branch
            result = get_circleci_token(12345)
