from unittest.mock import Mock, patch

import pytest

from services.supabase.coverages.update_issue_url import update_issue_url


class TestUpdateIssueUrl:
    """Test cases for update_issue_url function"""

    @pytest.fixture
    def mock_supabase_success(self):
        """Mock successful supabase response"""
        mock_response = Mock()
        mock_response.data = [
            {"id": 1, "github_issue_url": "https://github.com/owner/repo/issues/123"}
        ]

        with patch(
            "services.supabase.coverages.update_issue_url.supabase"
        ) as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = mock_response
            yield mock_supabase, mock_table

    @pytest.fixture
    def mock_supabase_empty_response(self):
        """Mock empty supabase response"""
        mock_response = Mock()
        mock_response.data = []

        with patch(
            "services.supabase.coverages.update_issue_url.supabase"
        ) as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = mock_response
            yield mock_supabase, mock_table

    def test_update_issue_url_success(self, mock_supabase_success):
        """Test successful update of issue URL"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = 123456
        file_path = "src/main.py"
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_supabase.table.assert_called_once_with("coverages")
        mock_table.update.assert_called_once_with(
            {"github_issue_url": github_issue_url}
        )
        mock_table.eq.assert_any_call("repo_id", repo_id)
        mock_table.eq.assert_any_call("full_path", file_path)
        mock_table.execute.assert_called_once()
        assert result == [{"id": 1, "github_issue_url": github_issue_url}]

    def test_update_issue_url_with_empty_response(self, mock_supabase_empty_response):
        """Test update with empty response data"""
        # Arrange
        mock_supabase, mock_table = mock_supabase_empty_response
        repo_id = 123456
        file_path = "src/main.py"
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_supabase.table.assert_called_once_with("coverages")
        mock_table.update.assert_called_once_with(
            {"github_issue_url": github_issue_url}
        )
        mock_table.eq.assert_any_call("repo_id", repo_id)
        mock_table.eq.assert_any_call("full_path", file_path)
        mock_table.execute.assert_called_once()
        assert result == []

    def test_update_issue_url_with_zero_repo_id(self, mock_supabase_success):
        """Test update with zero repo_id"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = 0
        file_path = "src/main.py"
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_table.eq.assert_any_call("repo_id", 0)
        assert result == [{"id": 1, "github_issue_url": github_issue_url}]

    def test_update_issue_url_with_negative_repo_id(self, mock_supabase_success):
        """Test update with negative repo_id"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = -1
        file_path = "src/main.py"
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_table.eq.assert_any_call("repo_id", -1)
        assert result == [{"id": 1, "github_issue_url": github_issue_url}]

    def test_update_issue_url_with_empty_file_path(self, mock_supabase_success):
        """Test update with empty file path"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = 123456
        file_path = ""
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_table.eq.assert_any_call("full_path", "")
        assert result == [{"id": 1, "github_issue_url": github_issue_url}]

    def test_update_issue_url_with_empty_github_url(self, mock_supabase_success):
        """Test update with empty GitHub issue URL"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = 123456
        file_path = "src/main.py"
        github_issue_url = ""

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_table.update.assert_called_once_with({"github_issue_url": ""})
        assert result == [
            {"id": 1, "github_issue_url": "https://github.com/owner/repo/issues/123"}
        ]

    def test_update_issue_url_with_long_file_path(self, mock_supabase_success):
        """Test update with very long file path"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = 123456
        file_path = "very/long/nested/directory/structure/with/many/levels/src/main.py"
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_table.eq.assert_any_call("full_path", file_path)
        assert result == [{"id": 1, "github_issue_url": github_issue_url}]

    def test_update_issue_url_with_special_characters_in_path(
        self, mock_supabase_success
    ):
        """Test update with special characters in file path"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = 123456
        file_path = "src/file-with_special.chars@123.py"
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_table.eq.assert_any_call("full_path", file_path)
        assert result == [{"id": 1, "github_issue_url": github_issue_url}]

    def test_update_issue_url_with_large_repo_id(self, mock_supabase_success):
        """Test update with very large repo_id"""
        # Arrange
        _, mock_table = mock_supabase_success
        repo_id = 999999999999
        file_path = "src/main.py"
        github_issue_url = "https://github.com/owner/repo/issues/123"

        # Act
        result = update_issue_url(repo_id, file_path, github_issue_url)

        # Assert
        mock_table.eq.assert_any_call("repo_id", repo_id)
        assert result == [{"id": 1, "github_issue_url": github_issue_url}]

    def test_update_issue_url_exception_handling(self):
        """Test that exceptions are handled properly by the decorator"""
        # Arrange
        with patch(
            "services.supabase.coverages.update_issue_url.supabase"
        ) as mock_supabase:
            mock_supabase.table.side_effect = Exception("Database error")

            # Act
            result = update_issue_url(
                123456, "src/main.py", "https://github.com/owner/repo/issues/123"
            )

            # Assert - The handle_exceptions decorator should return None on error
            assert result is None

    def test_update_issue_url_method_chaining(self, mock_supabase_success):
        """Test that the method chaining works correctly"""
        # Arrange
        _, mock_table = mock_supabase_success

        # Act
        update_issue_url(
            123456, "src/main.py", "https://github.com/owner/repo/issues/123"
        )

        # Assert - Verify the method chaining sequence
        assert mock_table.update.return_value == mock_table
        assert mock_table.eq.return_value == mock_table
        # The execute method should be called on the final chained object
        mock_table.execute.assert_called_once()
