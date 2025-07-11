# Standard imports
import unittest
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.supabase.issues.get_issue import get_issue
from schemas.supabase.fastapi.schema_public_latest import Issues


class TestGetIssue(unittest.TestCase):
    """Test cases for get_issue function"""

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
        
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_eq4 = MagicMock()
        
        # Chain the method calls
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.eq.return_value = mock_eq4
        mock_eq4.execute.return_value = (None, [mock_issue_data])

        # Execute
        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )

        # Assert
        self.assertIsInstance(result, dict)  # cast returns the original dict
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["owner_type"], "Organization")
        self.assertEqual(result["owner_name"], "test-owner")
        self.assertEqual(result["repo_name"], "test-repo")
        self.assertEqual(result["issue_number"], 123)
        
        # Verify the database query was constructed correctly
        mock_supabase.table.assert_called_once_with(table_name="issues")
        mock_table.select.assert_called_once_with("*")
        
        # Verify all the eq calls were made with correct parameters
        eq_calls = mock_select.eq.call_args_list
        self.assertEqual(len(eq_calls), 1)
        self.assertEqual(eq_calls[0], ((), {"column": "owner_type", "value": "Organization"}))

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_no_data_found(self, mock_supabase):
        """Test when no issue is found in the database"""
        # Setup
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_eq4 = MagicMock()
        
        # Chain the method calls
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.eq.return_value = mock_eq4
        mock_eq4.execute.return_value = (None, [])  # Empty result

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
        # Setup
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_eq4 = MagicMock()
        
        # Chain the method calls
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.eq.return_value = mock_eq4
        mock_eq4.execute.return_value = (None, [])

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
        
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_eq4 = MagicMock()
        
        # Chain the method calls
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.eq.return_value = mock_eq4
        mock_eq4.execute.return_value = (None, [mock_issue_data])

        # Execute
        result = get_issue(
            owner_type="User",
            owner_name="individual-user",
            repo_name="personal-repo",
            issue_number=789,
        )

        # Assert
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
        
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_eq4 = MagicMock()
        
        # Chain the method calls
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.eq.return_value = mock_eq4
        mock_eq4.execute.return_value = (None, [mock_issue_data])

        # Execute
        result = get_issue(
            owner_type="Organization",
            owner_name="test-org-with-dashes",
            repo_name="repo_with_underscores",
            issue_number=1,
        )

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["owner_name"], "test-org-with-dashes")
        self.assertEqual(result["repo_name"], "repo_with_underscores")


if __name__ == "__main__":
    unittest.main()
