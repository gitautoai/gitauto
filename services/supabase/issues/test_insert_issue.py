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


@pytest.fixture
def mock_issues_insert():
    """Fixture to provide a mocked IssuesInsert schema."""
    with patch("services.supabase.issues.insert_issue.IssuesInsert") as mock:
        mock_instance = MagicMock()
        mock_instance.model_dump.return_value = {
            "owner_id": TEST_OWNER_ID,
            "owner_type": TEST_OWNER_TYPE,
            "owner_name": TEST_OWNER_NAME,
            "repo_id": TEST_REPO_ID,
            "repo_name": TEST_REPO_NAME,
            "issue_number": TEST_ISSUE_NUMBER,
            "installation_id": TEST_INSTALLATION_ID,
        }
        mock.return_value = mock_instance
        yield mock


def test_insert_issue_success(mock_supabase, mock_issues_insert):
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

    # Verify IssuesInsert was called with correct parameters
    mock_issues_insert.assert_called_once_with(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        installation_id=TEST_INSTALLATION_ID,
    )

    # Verify model_dump was called with exclude_none=True
    mock_issues_insert.return_value.model_dump.assert_called_once_with(
        exclude_none=True
    )

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


def test_insert_issue_with_zero_values(mock_supabase, mock_issues_insert):
    """Test issue insertion with zero values for numeric fields."""
    # Arrange
    owner_id = 0
    repo_id = 0
    issue_number = 0
    installation_id = 0

    mock_issues_insert.return_value.model_dump.return_value = {
        "owner_id": owner_id,
        "owner_type": TEST_OWNER_TYPE,
        "owner_name": TEST_OWNER_NAME,
        "repo_id": repo_id,
        "repo_name": TEST_REPO_NAME,
        "issue_number": issue_number,
        "installation_id": installation_id,
    }

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
    mock_issues_insert.assert_called_once_with(
        owner_id=owner_id,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=repo_id,
        repo_name=TEST_REPO_NAME,
        issue_number=issue_number,
        installation_id=installation_id,
    )


def test_insert_issue_with_empty_strings(mock_supabase, mock_issues_insert):
    """Test issue insertion with empty string values."""
    # Arrange
    owner_type = ""
    owner_name = ""
    repo_name = ""

    mock_issues_insert.return_value.model_dump.return_value = {
        "owner_id": TEST_OWNER_ID,
        "owner_type": owner_type,
        "owner_name": owner_name,
        "repo_id": TEST_REPO_ID,
        "repo_name": repo_name,
        "issue_number": TEST_ISSUE_NUMBER,
        "installation_id": TEST_INSTALLATION_ID,
    }

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
    mock_issues_insert.assert_called_once_with(
        owner_id=TEST_OWNER_ID,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=TEST_REPO_ID,
        repo_name=repo_name,
        issue_number=TEST_ISSUE_NUMBER,
        installation_id=TEST_INSTALLATION_ID,
    )


def test_insert_issue_with_large_values(mock_supabase, mock_issues_insert):
    """Test issue insertion with large numeric values."""
    # Arrange
    large_owner_id = 9999999999
    large_repo_id = 9999999999
    large_issue_number = 9999999999
    large_installation_id = 9999999999

    mock_issues_insert.return_value.model_dump.return_value = {
        "owner_id": large_owner_id,
        "owner_type": TEST_OWNER_TYPE,
        "owner_name": TEST_OWNER_NAME,
        "repo_id": large_repo_id,
        "repo_name": TEST_REPO_NAME,
        "issue_number": large_issue_number,
        "installation_id": large_installation_id,
    }

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
    mock_issues_insert.assert_called_once_with(
        owner_id=large_owner_id,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=large_repo_id,
        repo_name=TEST_REPO_NAME,
        issue_number=large_issue_number,
        installation_id=large_installation_id,
    )


def test_insert_issue_with_negative_values(mock_supabase, mock_issues_insert):
    """Test issue insertion with negative values for numeric fields."""
    # Arrange
    negative_owner_id = -1
    negative_repo_id = -1
    negative_issue_number = -1
    negative_installation_id = -1

    mock_issues_insert.return_value.model_dump.return_value = {
        "owner_id": negative_owner_id,
        "owner_type": TEST_OWNER_TYPE,
        "owner_name": TEST_OWNER_NAME,
        "repo_id": negative_repo_id,
        "repo_name": TEST_REPO_NAME,
        "issue_number": negative_issue_number,
        "installation_id": negative_installation_id,
    }

    # Act
    result = insert_issue(
        owner_id=negative_owner_id,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=negative_repo_id,
        repo_name=TEST_REPO_NAME,
        issue_number=negative_issue_number,
        installation_id=negative_installation_id,
    )

    # Assert
    assert result is None
    mock_issues_insert.assert_called_once_with(
        owner_id=negative_owner_id,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=negative_repo_id,
        repo_name=TEST_REPO_NAME,
        issue_number=negative_issue_number,
        installation_id=negative_installation_id,
    )


def test_insert_issue_supabase_exception_raises(mock_supabase, mock_issues_insert):
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


def test_insert_issue_issues_insert_exception_raises(mock_supabase, mock_issues_insert):
    """Test that IssuesInsert exceptions are raised due to @handle_exceptions(raise_on_error=True)."""
    # Arrange
    mock_issues_insert.side_effect = ValueError("Invalid data")

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid data"):
        insert_issue(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            installation_id=TEST_INSTALLATION_ID,
        )


def test_insert_issue_model_dump_exception_raises(mock_supabase, mock_issues_insert):
    """Test that model_dump exceptions are raised due to @handle_exceptions(raise_on_error=True)."""
    # Arrange
    mock_issues_insert.return_value.model_dump.side_effect = AttributeError(
        "Model dump error"
    )

    # Act & Assert
    with pytest.raises(AttributeError, match="Model dump error"):
        insert_issue(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            installation_id=TEST_INSTALLATION_ID,
        )


def test_insert_issue_with_special_characters_in_strings(
    mock_supabase, mock_issues_insert
):
    """Test issue insertion with special characters in string fields."""
    # Arrange
    owner_type = "Organization!@#$%^&*()"
    owner_name = "test-owner-with-special-chars!@#$%"
    repo_name = "test-repo-with-special-chars!@#$%"

    mock_issues_insert.return_value.model_dump.return_value = {
        "owner_id": TEST_OWNER_ID,
        "owner_type": owner_type,
        "owner_name": owner_name,
        "repo_id": TEST_REPO_ID,
        "repo_name": repo_name,
        "issue_number": TEST_ISSUE_NUMBER,
        "installation_id": TEST_INSTALLATION_ID,
    }

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
    mock_issues_insert.assert_called_once_with(
        owner_id=TEST_OWNER_ID,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=TEST_REPO_ID,
        repo_name=repo_name,
        issue_number=TEST_ISSUE_NUMBER,
        installation_id=TEST_INSTALLATION_ID,
    )


def test_insert_issue_with_unicode_characters(mock_supabase, mock_issues_insert):
    """Test issue insertion with Unicode characters in string fields."""
    # Arrange
    owner_name = "测试用户"  # Chinese characters
    repo_name = "тест-репо"  # Cyrillic characters
    owner_type = "Organización"  # Spanish with accent

    mock_issues_insert.return_value.model_dump.return_value = {
        "owner_id": TEST_OWNER_ID,
        "owner_type": owner_type,
        "owner_name": owner_name,
        "repo_id": TEST_REPO_ID,
        "repo_name": repo_name,
        "issue_number": TEST_ISSUE_NUMBER,
        "installation_id": TEST_INSTALLATION_ID,
    }

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
    mock_issues_insert.assert_called_once_with(
        owner_id=TEST_OWNER_ID,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=TEST_REPO_ID,
        repo_name=repo_name,
        issue_number=TEST_ISSUE_NUMBER,
        installation_id=TEST_INSTALLATION_ID,
    )


def test_insert_issue_table_method_called_correctly(mock_supabase, mock_issues_insert):
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


def test_insert_issue_model_dump_exclude_none_behavior(
    mock_supabase, mock_issues_insert
):
    """Test that model_dump is called with exclude_none=True and handles None values correctly."""
    # Arrange - Mock model_dump to return data with some None values excluded
    mock_issues_insert.return_value.model_dump.return_value = {
        "owner_id": TEST_OWNER_ID,
        "owner_type": TEST_OWNER_TYPE,
        "owner_name": TEST_OWNER_NAME,
        "repo_id": TEST_REPO_ID,
        "repo_name": TEST_REPO_NAME,
        "issue_number": TEST_ISSUE_NUMBER,
        "installation_id": TEST_INSTALLATION_ID,
        # Note: Some fields might be excluded due to exclude_none=True
    }

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

    # Assert - Verify model_dump was called with exclude_none=True
    mock_issues_insert.return_value.model_dump.assert_called_once_with(
        exclude_none=True
    )
