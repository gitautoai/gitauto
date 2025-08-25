from unittest.mock import patch, MagicMock

import pytest

from config import (
    TEST_OWNER_ID,
    TEST_OWNER_TYPE,
    TEST_OWNER_NAME,
    TEST_REPO_ID,
    TEST_REPO_NAME,
    TEST_ISSUE_NUMBER,
    TEST_INSTALLATION_ID,
)
from services.supabase.issues.insert_issue import insert_issue


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked Supabase client."""
    with patch("services.supabase.issues.insert_issue.supabase") as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        MagicMock()

        mock.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = None

        yield mock


def test_insert_issue_success(mock_supabase):
    """Test successful issue insertion with all required parameters."""
    # Act
    result = insert_issue(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        installation_id=TEST_INSTALLATION_ID,
    )

    # Assert
    assert result is None  # Function returns None when successful

    # Verify supabase operations were called correctly
    mock_supabase.table.assert_called_once_with(table_name="issues")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        json={
            "owner_id": TEST_OWNER_ID,
            "owner_type": TEST_OWNER_TYPE,
            "owner_name": TEST_OWNER_NAME,
            "repo_id": TEST_REPO_ID,
            "repo_name": TEST_REPO_NAME,
            "issue_number": TEST_ISSUE_NUMBER,
            "installation_id": TEST_INSTALLATION_ID,
        }
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_issue_with_zero_values(mock_supabase):
    """Test issue insertion with zero values for numeric fields."""
    # Arrange
    owner_id = 0
    repo_id = 0
    issue_number = 0
    installation_id = 0

    # Act
    result = insert_issue(
        owner_id=owner_id,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=repo_id,
        repo_name=TEST_REPO_NAME,
        issue_number=issue_number,
        installation_id=installation_id,
    )

    # Assert
    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="issues")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        json={
            "owner_id": owner_id,
            "owner_type": TEST_OWNER_TYPE,
            "owner_name": TEST_OWNER_NAME,
            "repo_id": repo_id,
            "repo_name": TEST_REPO_NAME,
            "issue_number": issue_number,
            "installation_id": installation_id,
        }
    )


def test_insert_issue_with_empty_strings(mock_supabase):
    """Test issue insertion with empty string values."""
    # Arrange
    owner_type = ""
    owner_name = ""
    repo_name = ""

    # Act
    result = insert_issue(
        owner_id=TEST_OWNER_ID,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=TEST_REPO_ID,
        repo_name=repo_name,
        issue_number=TEST_ISSUE_NUMBER,
        installation_id=TEST_INSTALLATION_ID,
    )

    # Assert
    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="issues")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        json={
            "owner_id": TEST_OWNER_ID,
            "owner_type": owner_type,
            "owner_name": owner_name,
            "repo_id": TEST_REPO_ID,
            "repo_name": repo_name,
            "issue_number": TEST_ISSUE_NUMBER,
            "installation_id": TEST_INSTALLATION_ID,
        }
    )


def test_insert_issue_with_large_values(mock_supabase):
    """Test issue insertion with large numeric values."""
    # Arrange
    large_owner_id = 9999999999
    large_repo_id = 9999999999
    large_issue_number = 9999999999
    large_installation_id = 9999999999

    # Act
    result = insert_issue(
        owner_id=large_owner_id,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=large_repo_id,
        repo_name=TEST_REPO_NAME,
        issue_number=large_issue_number,
        installation_id=large_installation_id,
    )

    # Assert
    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="issues")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        json={
            "owner_id": large_owner_id,
            "owner_type": TEST_OWNER_TYPE,
            "owner_name": TEST_OWNER_NAME,
            "repo_id": large_repo_id,
            "repo_name": TEST_REPO_NAME,
            "issue_number": large_issue_number,
            "installation_id": large_installation_id,
        }
    )


def test_insert_issue_supabase_exception_raises(mock_supabase):
    """Test that Supabase exceptions are raised due to @handle_exceptions(raise_on_error=True)."""
    # Arrange
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
        Exception("Database error")
    )

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        insert_issue(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            installation_id=TEST_INSTALLATION_ID,
        )


def test_insert_issue_table_method_called_correctly(mock_supabase):
    """Test that the supabase table method is called with the correct table name."""
    # Act
    insert_issue(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        installation_id=TEST_INSTALLATION_ID,
    )

    # Assert - Verify table method is called with correct table name
    mock_supabase.table.assert_called_once_with(table_name="issues")
