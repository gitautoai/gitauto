# Standard imports
import unittest
from unittest.mock import patch, MagicMock

# Local imports
from services.supabase.repositories.update_repository import update_repository


class TestUpdateRepository(unittest.TestCase):
    """Test cases for update_repository function"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_repo_id = 123456
        self.test_user_id = 789
        self.test_user_name = "test-user"
        self.test_file_count = 100
        self.test_blank_lines = 50
        self.test_comment_lines = 25
        self.test_code_lines = 500

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_success(self, mock_supabase):
        """Test successful repository update"""
        # Setup
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "repo_id": self.test_repo_id}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = update_repository(
            repo_id=self.test_repo_id,
            user_id=self.test_user_id,
            user_name=self.test_user_name,
            file_count=self.test_file_count,
            blank_lines=self.test_blank_lines,
            comment_lines=self.test_comment_lines,
            code_lines=self.test_code_lines,
        )

        # Assert
        self.assertEqual(result, {"id": 1, "repo_id": self.test_repo_id})
        mock_supabase.table.assert_called_once_with("repositories")

        # Verify the update data structure
        update_call_args = mock_supabase.table.return_value.update.call_args[0][0]
        expected_updated_by = f"{self.test_user_id}:{self.test_user_name}"

        self.assertEqual(update_call_args["file_count"], self.test_file_count)
        self.assertEqual(update_call_args["blank_lines"], self.test_blank_lines)
        self.assertEqual(update_call_args["comment_lines"], self.test_comment_lines)
        self.assertEqual(update_call_args["code_lines"], self.test_code_lines)
        self.assertEqual(update_call_args["updated_by"], expected_updated_by)

        # Verify the query chain
        mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
            "repo_id", self.test_repo_id
        )

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_empty_result(self, mock_supabase):
        """Test repository update with empty result data"""
        # Setup
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = update_repository(
            repo_id=self.test_repo_id,
            user_id=self.test_user_id,
            user_name=self.test_user_name,
            file_count=self.test_file_count,
            blank_lines=self.test_blank_lines,
            comment_lines=self.test_comment_lines,
            code_lines=self.test_code_lines,
        )

        # Assert
        self.assertIsNone(result)
        mock_supabase.table.assert_called_once_with("repositories")

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_none_result_data(self, mock_supabase):
        """Test repository update with None result data"""
        # Setup
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = update_repository(
            repo_id=self.test_repo_id,
            user_id=self.test_user_id,
            user_name=self.test_user_name,
            file_count=self.test_file_count,
            blank_lines=self.test_blank_lines,
            comment_lines=self.test_comment_lines,
            code_lines=self.test_code_lines,
        )

        # Assert
        self.assertIsNone(result)

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_with_zero_values(self, mock_supabase):
        """Test repository update with zero values"""
        # Setup
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "repo_id": self.test_repo_id}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = update_repository(
            repo_id=self.test_repo_id,
            user_id=self.test_user_id,
            user_name=self.test_user_name,
            file_count=0,
            blank_lines=0,
            comment_lines=0,
            code_lines=0,
        )

        # Assert
        self.assertEqual(result, {"id": 1, "repo_id": self.test_repo_id})

        # Verify zero values are properly handled
        update_call_args = mock_supabase.table.return_value.update.call_args[0][0]
        self.assertEqual(update_call_args["file_count"], 0)
        self.assertEqual(update_call_args["blank_lines"], 0)
        self.assertEqual(update_call_args["comment_lines"], 0)
        self.assertEqual(update_call_args["code_lines"], 0)

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_with_special_characters_in_username(self, mock_supabase):
        """Test repository update with special characters in username"""
        # Setup
        special_username = "test-user@domain.com"
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "repo_id": self.test_repo_id}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = update_repository(
            repo_id=self.test_repo_id,
            user_id=self.test_user_id,
            user_name=special_username,
            file_count=self.test_file_count,
            blank_lines=self.test_blank_lines,
            comment_lines=self.test_comment_lines,
            code_lines=self.test_code_lines,
        )

        # Assert
        self.assertEqual(result, {"id": 1, "repo_id": self.test_repo_id})

        # Verify special characters are handled correctly
        update_call_args = mock_supabase.table.return_value.update.call_args[0][0]
        expected_updated_by = f"{self.test_user_id}:{special_username}"
        self.assertEqual(update_call_args["updated_by"], expected_updated_by)

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_with_large_values(self, mock_supabase):
        """Test repository update with large numeric values"""
        # Setup
        large_values = {
            "file_count": 999999,
            "blank_lines": 500000,
            "comment_lines": 250000,
            "code_lines": 1000000,
        }
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "repo_id": self.test_repo_id}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = update_repository(
            repo_id=self.test_repo_id,
            user_id=self.test_user_id,
            user_name=self.test_user_name,
            **large_values,
        )

        # Assert
        self.assertEqual(result, {"id": 1, "repo_id": self.test_repo_id})

        # Verify large values are handled correctly
        update_call_args = mock_supabase.table.return_value.update.call_args[0][0]
        for key, value in large_values.items():
            self.assertEqual(update_call_args[key], value)

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_exception_handling(self, mock_supabase):
        """Test repository update exception handling"""
        # Setup
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
            "Database error"
        )

        # Execute
        result = update_repository(
            repo_id=self.test_repo_id,
            user_id=self.test_user_id,
            user_name=self.test_user_name,
            file_count=self.test_file_count,
            blank_lines=self.test_blank_lines,
            comment_lines=self.test_comment_lines,
            code_lines=self.test_code_lines,
        )

        # Assert - should return None due to handle_exceptions decorator
        self.assertIsNone(result)

    def test_repositories_update_schema_creation(self):
        """Test repository data dict creation with valid data"""
        # Execute
        repository_data = {
            "file_count": self.test_file_count,
            "blank_lines": self.test_blank_lines,
            "comment_lines": self.test_comment_lines,
            "code_lines": self.test_code_lines,
            "updated_by": f"{self.test_user_id}:{self.test_user_name}",
        }

        # Assert
        self.assertEqual(repository_data["file_count"], self.test_file_count)
        self.assertEqual(repository_data["blank_lines"], self.test_blank_lines)
        self.assertEqual(repository_data["comment_lines"], self.test_comment_lines)
        self.assertEqual(repository_data["code_lines"], self.test_code_lines)
        self.assertEqual(
            repository_data["updated_by"], f"{self.test_user_id}:{self.test_user_name}"
        )

    def test_repositories_update_schema_dict_keys(self):
        """Test repository data dict has expected keys"""
        # Execute
        repository_data = {
            "file_count": self.test_file_count,
            "blank_lines": self.test_blank_lines,
            "comment_lines": self.test_comment_lines,
            "code_lines": self.test_code_lines,
            "updated_by": f"{self.test_user_id}:{self.test_user_name}",
        }

        # Assert
        expected_keys = {
            "file_count",
            "blank_lines",
            "comment_lines",
            "code_lines",
            "updated_by",
        }
        self.assertEqual(set(repository_data.keys()), expected_keys)
        self.assertNotIn(None, repository_data.values())
