# Standard imports
import unittest
from unittest.mock import patch, MagicMock
from typing import Any, Dict, List

# Third-party imports

# Local imports
from services.supabase.issues.get_issue import get_issue


class TestGetIssue(unittest.TestCase):
    """Test cases for get_issue function"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_issue_data = {
            "id": 1,
            "owner_type": "Organization",
            "owner_name": "test-owner",
            "repo_name": "test-repo",
            "issue_number": 123,
            "installation_id": 456,
            "merged": False,
            "created_at": "2024-01-01T00:00:00Z",
            "owner_id": 789,
            "repo_id": 101112,
            "created_by": "test-user",
            "run_id": None,
        }

        self.test_params = {
            "owner_type": "Organization",
            "owner_name": "test-owner",
            "repo_name": "test-repo",
            "issue_number": 123,
        }

    def _setup_supabase_mock(
        self, mock_supabase: MagicMock, return_data: List[Dict[str, Any]]
    ):
        """Helper method to set up the supabase mock chain"""
        mock_chain = (
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value
        )
        mock_chain.execute.return_value = ((None, return_data), None)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_success_with_data(self, mock_supabase):
        """Test successful issue retrieval when data exists"""
        # Setup
        mock_issue_data = {
            "id": 1,
            "owner_type": "Organization",
            "owner_name": "test-owner",
            "repo_name": "test-repo",
            "issue_number": 123,
            "installation_id": 456,
            "merged": False,
            "created_at": "2024-01-01T00:00:00Z",
            "owner_id": 789,
            "repo_id": 101112,
            "created_by": "test-user",
            "run_id": None,
        }

        self._setup_supabase_mock(mock_supabase, [mock_issue_data])

        # Execute
        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )

        # Assert
        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["owner_type"], "Organization")
        self.assertEqual(result["owner_name"], "test-owner")
        self.assertEqual(result["repo_name"], "test-repo")
        self.assertEqual(result["issue_number"], 123)

        # Verify the database query was constructed correctly
        mock_supabase.table.assert_called_once_with(table_name="issues")
        mock_supabase.table.return_value.select.assert_called_once_with("*")

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_no_data_found(self, mock_supabase):
        """Test when no issue is found in the database"""
        self._setup_supabase_mock(mock_supabase, [])  # Empty result

        # Execute
        result = get_issue(
            owner_type="Organization",
            owner_name="nonexistent-owner",
            repo_name="nonexistent-repo",
            issue_number=999,
        )

        # Assert
        self.assertIsNone(result)
        mock_supabase.table.assert_called_once_with(table_name="issues")

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_empty_data_list(self, mock_supabase):
        """Test when data[1] is an empty list"""
        self._setup_supabase_mock(mock_supabase, [])

        # Execute
        result = get_issue(
            owner_type="User",
            owner_name="test-user",
            repo_name="test-repo",
            issue_number=456,
        )

        # Assert
        self.assertIsNone(result)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_different_owner_types(self, mock_supabase):
        """Test with different owner types (User vs Organization)"""
        # Setup
        mock_issue_data = {
            "id": 2,
            "owner_type": "User",
            "owner_name": "individual-user",
            "repo_name": "personal-repo",
            "issue_number": 789,
            "installation_id": 123,
            "merged": True,
            "created_at": "2024-02-01T00:00:00Z",
            "owner_id": 456,
            "repo_id": 789012,
            "created_by": "individual-user",
            "run_id": 999,
        }

        self._setup_supabase_mock(mock_supabase, [mock_issue_data])

        # Execute
        result = get_issue(
            owner_type="User",
            owner_name="individual-user",
            repo_name="personal-repo",
            issue_number=789,
        )

        # Assert
        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["owner_type"], "User")
        self.assertEqual(result["merged"], True)
        self.assertEqual(result["run_id"], 999)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_database_exception(self, mock_supabase):
        """Test that exceptions are handled gracefully due to handle_exceptions decorator"""
        # Setup
        mock_supabase.table.side_effect = Exception("Database connection error")

        # Execute
        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )

        # Assert - should return None due to handle_exceptions decorator
        self.assertIsNone(result)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_special_characters(self, mock_supabase):
        """Test with special characters in parameters"""
        # Setup
        mock_issue_data = {
            "id": 3,
            "owner_type": "Organization",
            "owner_name": "test-org-with-dashes",
            "repo_name": "repo_with_underscores",
            "issue_number": 1,
            "installation_id": 789,
            "merged": False,
            "created_at": "2024-03-01T00:00:00Z",
            "owner_id": 111,
            "repo_id": 222,
            "created_by": "test-user",
            "run_id": None,
        }

        self._setup_supabase_mock(mock_supabase, [mock_issue_data])

        # Execute
        result = get_issue(
            owner_type="Organization",
            owner_name="test-org-with-dashes",
            repo_name="repo_with_underscores",
            issue_number=1,
        )

        # Assert
        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["owner_name"], "test-org-with-dashes")
        self.assertEqual(result["repo_name"], "repo_with_underscores")

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_query_parameters_validation(self, mock_supabase):
        """Test that all query parameters are passed correctly to the database"""
        self._setup_supabase_mock(mock_supabase, [self.sample_issue_data])

        # Execute
        get_issue(**self.test_params)

        # Verify the complete query chain
        mock_supabase.table.assert_called_once_with(table_name="issues")

        # Get the mock chain to verify eq calls
        mock_chain = mock_supabase.table.return_value.select.return_value

        # Verify select was called
        mock_supabase.table.return_value.select.assert_called_once_with("*")

        # The eq calls are chained, so we verify execute was called
        final_mock = (
            mock_chain.eq.return_value.eq.return_value.eq.return_value.eq.return_value
        )
        final_mock.execute.assert_called_once()

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_zero_issue_number(self, mock_supabase):
        """Test with issue number 0"""
        issue_data = self.sample_issue_data.copy()
        issue_data["issue_number"] = 0
        self._setup_supabase_mock(mock_supabase, [issue_data])

        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            issue_number=0,
        )

        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["issue_number"], 0)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_large_issue_number(self, mock_supabase):
        """Test with a very large issue number"""
        large_issue_number = 999999999
        issue_data = self.sample_issue_data.copy()
        issue_data["issue_number"] = large_issue_number
        self._setup_supabase_mock(mock_supabase, [issue_data])

        result = get_issue(
            owner_type="User",
            owner_name="test-user",
            repo_name="test-repo",
            issue_number=large_issue_number,
        )

        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["issue_number"], large_issue_number)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_returns_first_result_only(self, mock_supabase):
        """Test that only the first result is returned when multiple results exist"""
        # Setup multiple results (though this shouldn't happen in practice due to unique constraints)
        first_issue = self.sample_issue_data.copy()
        second_issue = self.sample_issue_data.copy()
        second_issue["id"] = 2
        second_issue["created_at"] = "2024-02-01T00:00:00Z"

        self._setup_supabase_mock(mock_supabase, [first_issue, second_issue])

        result = get_issue(**self.test_params)

        # Should return the first result
        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 1)  # First issue's ID
        self.assertEqual(
            result["created_at"], "2024-01-01T00:00:00Z"
        )  # First issue's date

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_returns_correct_data_structure(self, mock_supabase):
        """Test that the function returns the correct data structure"""
        self._setup_supabase_mock(mock_supabase, [self.sample_issue_data])

        result = get_issue(**self.test_params)

        # The cast function from typing just returns the value as-is
        self.assertEqual(result, self.sample_issue_data)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_none_values(self, mock_supabase):
        """Test behavior when some fields in the result are None"""
        issue_data_with_nones = self.sample_issue_data.copy()
        issue_data_with_nones["run_id"] = None
        issue_data_with_nones["created_by"] = None

        self._setup_supabase_mock(mock_supabase, [issue_data_with_nones])

        result = get_issue(**self.test_params)

        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertIsNone(result["run_id"])
        self.assertIsNone(result["created_by"])

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_supabase_execute_exception(self, mock_supabase):
        """Test exception handling when execute() fails"""
        # Setup mock to raise exception on execute
        mock_chain = (
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value
        )
        mock_chain.execute.side_effect = Exception("Supabase execute error")

        result = get_issue(**self.test_params)

        # Should return None due to handle_exceptions decorator
        self.assertIsNone(result)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_minimal_required_fields(self, mock_supabase):
        """Test with minimal required fields in the response"""
        minimal_issue_data = {
            "id": 999,
            "owner_type": "Organization",
            "owner_name": "minimal-owner",
            "repo_name": "minimal-repo",
            "issue_number": 1,
            "installation_id": 123,
            "merged": False,
            "created_at": "2024-01-01T00:00:00Z",
            "owner_id": 456,
            "repo_id": 789,
        }

        self._setup_supabase_mock(mock_supabase, [minimal_issue_data])

        result = get_issue(
            owner_type="Organization",
            owner_name="minimal-owner",
            repo_name="minimal-repo",
            issue_number=1,
        )

        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 999)
        self.assertEqual(result["owner_type"], "Organization")


if __name__ == "__main__":
    unittest.main()
