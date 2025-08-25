import json
from unittest.mock import patch, MagicMock

import pytest
import requests

from config import (
    TEST_OWNER_TYPE,
    TEST_OWNER_NAME,
    TEST_REPO_NAME,
    TEST_ISSUE_NUMBER,
)
from services.supabase.issues.update_issue_merged import update_issue_merged


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.issues.update_issue_merged.supabase") as mock:
        yield mock


@pytest.fixture
def sample_parameters():
    """Fixture providing sample parameters for the function."""
    return {
        "owner_type": TEST_OWNER_TYPE,
        "owner_name": TEST_OWNER_NAME,
        "repo_name": TEST_REPO_NAME,
        "issue_number": TEST_ISSUE_NUMBER,
        "merged": True,
    }


class TestUpdateIssueMerged:
    """Test cases for update_issue_merged function."""

    def test_update_issue_merged_success_with_default_merged_true(
        self, mock_supabase, sample_parameters
    ):
        """Test successful update with default merged=True."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        # Act - call without merged parameter to test default
        update_issue_merged(
            owner_type=sample_parameters["owner_type"],
            owner_name=sample_parameters["owner_name"],
            repo_name=sample_parameters["repo_name"],
            issue_number=sample_parameters["issue_number"],
        )

        # Assert
        mock_supabase.table.assert_called_once_with(table_name="issues")
        mock_table.update.assert_called_once_with(json={"merged": True})

        # Verify the chain of eq calls
        eq_calls = mock_update.eq.call_args_list + mock_eq_chain.eq.call_args_list
        assert len(eq_calls) == 4

        # Check that all expected eq calls were made with keyword arguments
        expected_calls = [
            {"column": "owner_type", "value": TEST_OWNER_TYPE},
            {"column": "owner_name", "value": TEST_OWNER_NAME},
            {"column": "repo_name", "value": TEST_REPO_NAME},
            {"column": "issue_number", "value": TEST_ISSUE_NUMBER},
        ]

        for expected_call in expected_calls:
            assert expected_call in [call[1] for call in eq_calls]

        mock_eq_chain.execute.assert_called_once()

    def test_update_issue_merged_success_with_merged_true(
        self, mock_supabase, sample_parameters
    ):
        """Test successful update with merged=True explicitly."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        # Act
        update_issue_merged(**sample_parameters)

        # Assert
        mock_supabase.table.assert_called_once_with(table_name="issues")
        mock_table.update.assert_called_once_with(json={"merged": True})
        mock_eq_chain.execute.assert_called_once()

    def test_update_issue_merged_success_with_merged_false(
        self, mock_supabase, sample_parameters
    ):
        """Test successful update with merged=False."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        # Modify parameters to set merged=False
        params = sample_parameters.copy()
        params["merged"] = False

        # Act
        update_issue_merged(**params)

        # Assert
        mock_supabase.table.assert_called_once_with(table_name="issues")
        mock_table.update.assert_called_once_with(json={"merged": False})
        mock_eq_chain.execute.assert_called_once()

    def test_update_issue_merged_with_different_owner_types(self, mock_supabase):
        """Test function with different owner types."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        owner_types = ["User", "Organization", "Bot"]

        for owner_type in owner_types:
            # Reset mocks for each iteration
            mock_update.reset_mock()
            mock_eq_chain.reset_mock()
            # Act
            update_issue_merged(
                owner_type=owner_type,
                owner_name="test_owner",
                repo_name="test_repo",
                issue_number=123,
            )

            # Assert that the correct owner_type was used
            eq_calls = mock_update.eq.call_args_list + mock_eq_chain.eq.call_args_list
            owner_type_call = next(
                call for call in eq_calls if call[1].get("column") == "owner_type"
            )
            assert owner_type_call[1]["value"] == owner_type

    def test_update_issue_merged_with_various_issue_numbers(self, mock_supabase):
        """Test function with various issue number values."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        issue_numbers = [1, 999, 12345, 999999]

        for issue_number in issue_numbers:
            # Reset mocks for each iteration
            mock_update.reset_mock()
            mock_eq_chain.reset_mock()
            # Act
            update_issue_merged(
                owner_type="Organization",
                owner_name="test_owner",
                repo_name="test_repo",
                issue_number=issue_number,
            )

            # Assert that the correct issue_number was used
            eq_calls = mock_update.eq.call_args_list + mock_eq_chain.eq.call_args_list
            issue_number_call = next(
                call for call in eq_calls if call[1].get("column") == "issue_number"
            )
            assert issue_number_call[1]["value"] == issue_number

    def test_update_issue_merged_with_special_characters_in_names(self, mock_supabase):
        """Test function with special characters in owner and repo names."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        test_cases = [
            ("owner-with-dashes", "repo-with-dashes"),
            ("owner_with_underscores", "repo_with_underscores"),
            ("owner.with.dots", "repo.with.dots"),
            ("owner123", "repo456"),
            ("UPPERCASE", "REPO"),
        ]

        for owner_name, repo_name in test_cases:
            # Reset mocks for each iteration
            mock_update.reset_mock()
            mock_eq_chain.reset_mock()
            # Act
            update_issue_merged(
                owner_type="Organization",
                owner_name=owner_name,
                repo_name=repo_name,
                issue_number=1,
            )

            # Assert that the correct names were used
            eq_calls = mock_update.eq.call_args_list + mock_eq_chain.eq.call_args_list

            owner_name_call = next(
                call for call in eq_calls if call[1].get("column") == "owner_name"
            )
            assert owner_name_call[1]["value"] == owner_name

            repo_name_call = next(
                call for call in eq_calls if call[1].get("column") == "repo_name"
            )
            assert repo_name_call[1]["value"] == repo_name

    def test_update_issue_merged_exception_handling_returns_none(self, mock_supabase):
        """Test that function returns None when an exception occurs."""
        # Arrange
        mock_supabase.table.side_effect = Exception("Database connection error")

        # Act
        result = update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
        )

        # Assert
        assert result is None

    def test_update_issue_merged_http_error_500_returns_none(self, mock_supabase):
        """Test that function returns None when HTTP 500 error occurs."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"

        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_supabase.table.side_effect = http_error

        # Act
        result = update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
        )

        # Assert
        assert result is None

    def test_update_issue_merged_http_error_other_returns_none(self, mock_supabase):
        """Test that function returns None when other HTTP errors occur."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Resource not found"

        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_supabase.table.side_effect = http_error

        # Act
        result = update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
        )

        # Assert
        assert result is None

    def test_update_issue_merged_json_decode_error_returns_none(self, mock_supabase):
        """Test that function returns None when JSON decode error occurs."""
        # Arrange
        json_error = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_supabase.table.side_effect = json_error

        # Act
        result = update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
        )

        # Assert
        assert result is None

    def test_update_issue_merged_attribute_error_returns_none(self, mock_supabase):
        """Test that function returns None when AttributeError occurs."""
        # Arrange
        mock_supabase.table.side_effect = AttributeError("Attribute not found")

        # Act
        result = update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
        )

        # Assert
        assert result is None

    def test_update_issue_merged_key_error_returns_none(self, mock_supabase):
        """Test that function returns None when KeyError occurs."""
        # Arrange
        mock_supabase.table.side_effect = KeyError("Key not found")

        # Act
        result = update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
        )

        # Assert
        assert result is None

    def test_update_issue_merged_type_error_returns_none(self, mock_supabase):
        """Test that function returns None when TypeError occurs."""
        # Arrange
        mock_supabase.table.side_effect = TypeError("Type error")

        # Act
        result = update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
        )

        # Assert
        assert result is None

    def test_update_issue_merged_supabase_query_structure(self, mock_supabase):
        """Test that the correct Supabase query structure is constructed."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        # Act
        update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
            merged=True,
        )

        # Assert the complete query chain
        mock_supabase.table.assert_called_once_with(table_name="issues")
        mock_table.update.assert_called_once_with(json={"merged": True})
        mock_eq_chain.execute.assert_called_once()

    @pytest.mark.parametrize("merged_value", [True, False])
    def test_update_issue_merged_with_parametrized_merged_values(
        self, mock_supabase, merged_value
    ):
        """Test function with various merged values using parametrize."""
        # Arrange
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq_chain = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_chain
        mock_eq_chain.eq.return_value = mock_eq_chain
        mock_eq_chain.execute.return_value = MagicMock()

        # Act
        update_issue_merged(
            owner_type="Organization",
            owner_name="test_owner",
            repo_name="test_repo",
            issue_number=123,
            merged=merged_value,
        )

        # Assert
        mock_table.update.assert_called_once_with(json={"merged": merged_value})
