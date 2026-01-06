# pylint: disable=unused-argument,too-many-instance-attributes
import unittest
from unittest.mock import patch, MagicMock

from services.supabase.repositories.update_repository import update_repository


class TestUpdateRepository(unittest.TestCase):
    """Test cases for update_repository function"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_owner_id = 789
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
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "repo_id": self.test_repo_id}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = update_repository(
            owner_id=self.test_owner_id,
            repo_id=self.test_repo_id,
            updated_by=f"{self.test_user_id}:{self.test_user_name}",
            file_count=self.test_file_count,
        )

        self.assertEqual(result, {"id": 1, "repo_id": self.test_repo_id})
        mock_supabase.table.assert_called_once_with("repositories")

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_empty_result(self, mock_supabase):
        """Test repository update with empty result data"""
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = update_repository(
            owner_id=self.test_owner_id,
            repo_id=self.test_repo_id,
            updated_by=f"{self.test_user_id}:{self.test_user_name}",
        )

        self.assertIsNone(result)

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_none_result_data(self, mock_supabase):
        """Test repository update with None result data"""
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = update_repository(
            owner_id=self.test_owner_id,
            repo_id=self.test_repo_id,
            updated_by=f"{self.test_user_id}:{self.test_user_name}",
        )

        self.assertIsNone(result)

    @patch("services.supabase.repositories.update_repository.supabase")
    def test_update_repository_exception_handling(self, mock_supabase):
        """Test repository update exception handling"""
        mock_supabase.table.side_effect = Exception("Database error")

        result = update_repository(
            owner_id=self.test_owner_id,
            repo_id=self.test_repo_id,
            updated_by=f"{self.test_user_id}:{self.test_user_name}",
        )

        self.assertIsNone(result)
