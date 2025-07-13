# Standard imports
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Local imports
from services.supabase.usage.count_completed_unique_requests import count_completed_unique_requests


class TestCountCompletedUniqueRequests(unittest.TestCase):
    """Test cases for count_completed_unique_requests function"""

    def _setup_supabase_mock(self, mock_supabase: MagicMock, return_data: list):
        """Helper method to set up the supabase mock chain"""
        mock_chain = mock_supabase.table.return_value.select.return_value.gt.return_value.eq.return_value.in_.return_value.eq.return_value
        mock_chain.execute.return_value = ((None, return_data), None)

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_success(self, mock_supabase):
        """Test successful retrieval and processing of unique requests"""
        # Setup
        mock_data = [
            {
                "owner_type": "Organization",
                "owner_name": "test-org",
                "repo_name": "test-repo",
                "issue_number": 1
            },
            {
                "owner_type": "User",
                "owner_name": "test-user",
                "repo_name": "another-repo",
                "issue_number": 2
            }
        ]
        self._setup_supabase_mock(mock_supabase, mock_data)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {
            "Organization/test-org/test-repo#1",
            "User/test-user/another-repo#2"
        }
        self.assertEqual(result, expected_unique_requests)
        
        # Verify the query chain was called correctly
        mock_supabase.table.assert_called_once_with("usage")
        mock_supabase.table.return_value.select.assert_called_once_with("owner_type, owner_name, repo_name, issue_number")
        mock_supabase.table.return_value.select.return_value.gt.assert_called_once_with("created_at", start_date)
        mock_supabase.table.return_value.select.return_value.gt.return_value.eq.assert_called_once_with("installation_id", installation_id)
        mock_supabase.table.return_value.select.return_value.gt.return_value.eq.return_value.in_.assert_called_once_with(
            "trigger", ["issue_comment", "issue_label", "pull_request"]
        )
        mock_supabase.table.return_value.select.return_value.gt.return_value.eq.return_value.in_.return_value.eq.assert_called_once_with("is_completed", True)

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_empty_result(self, mock_supabase):
        """Test handling of empty result from database"""
        # Setup
        self._setup_supabase_mock(mock_supabase, [])
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        self.assertEqual(result, set())

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_duplicate_records(self, mock_supabase):
        """Test deduplication of identical requests"""
        # Setup
        mock_data = [
            {
                "owner_type": "Organization",
                "owner_name": "test-org",
                "repo_name": "test-repo",
                "issue_number": 1
            },
            {
                "owner_type": "Organization",
                "owner_name": "test-org",
                "repo_name": "test-repo",
                "issue_number": 1
            },  # Duplicate
            {
                "owner_type": "User",
                "owner_name": "test-user",
                "repo_name": "another-repo",
                "issue_number": 2
            }
        ]
        self._setup_supabase_mock(mock_supabase, mock_data)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert - should only contain unique requests
        expected_unique_requests = {
            "Organization/test-org/test-repo#1",
            "User/test-user/another-repo#2"
        }
        self.assertEqual(result, expected_unique_requests)
        self.assertEqual(len(result), 2)  # Ensure duplicates are removed

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_different_issue_numbers(self, mock_supabase):
        """Test that different issue numbers in same repo create unique requests"""
        # Setup
        mock_data = [
            {
                "owner_type": "Organization",
                "owner_name": "test-org",
                "repo_name": "test-repo",
                "issue_number": 1
            },
            {
                "owner_type": "Organization",
                "owner_name": "test-org",
                "repo_name": "test-repo",
                "issue_number": 2
            }
        ]
        self._setup_supabase_mock(mock_supabase, mock_data)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {
            "Organization/test-org/test-repo#1",
            "Organization/test-org/test-repo#2"
        }
        self.assertEqual(result, expected_unique_requests)
        self.assertEqual(len(result), 2)

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_database_error(self, mock_supabase):
        """Test error handling when database query fails"""
        # Setup
        mock_supabase.table.side_effect = Exception("Database error")
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert - should return default value (empty set) due to handle_exceptions decorator
        self.assertEqual(result, set())

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_with_special_characters(self, mock_supabase):
        """Test handling of special characters in owner/repo names"""
        # Setup
        mock_data = [
            {
                "owner_type": "Organization",
                "owner_name": "test-org-with-dashes",
                "repo_name": "test.repo.with.dots",
                "issue_number": 1
            },
            {
                "owner_type": "User",
                "owner_name": "test_user_with_underscores",
                "repo_name": "repo-with-numbers-123",
                "issue_number": 42
            }
        ]
        self._setup_supabase_mock(mock_supabase, mock_data)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {
            "Organization/test-org-with-dashes/test.repo.with.dots#1",
            "User/test_user_with_underscores/repo-with-numbers-123#42"
        }
        self.assertEqual(result, expected_unique_requests)

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_query_parameters(self, mock_supabase):
        """Test that query parameters are passed correctly"""
        # Setup
        self._setup_supabase_mock(mock_supabase, [])
        
        installation_id = 98765
        start_date = datetime(2023, 6, 15, 10, 30, 45)
        
        # Execute
        count_completed_unique_requests(installation_id, start_date)
        
        # Assert that the correct parameters were used in the query
        mock_supabase.table.return_value.select.return_value.gt.assert_called_once_with("created_at", start_date)
        mock_supabase.table.return_value.select.return_value.gt.return_value.eq.assert_called_once_with("installation_id", installation_id)

    @patch("services.supabase.usage.count_completed_unique_requests.supabase")
    def test_count_completed_unique_requests_trigger_filter(self, mock_supabase):
        """Test that the correct trigger types are filtered"""
        # Setup
        self._setup_supabase_mock(mock_supabase, [])
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        count_completed_unique_requests(installation_id, start_date)
        
        # Assert that the correct trigger types are filtered
        mock_supabase.table.return_value.select.return_value.gt.return_value.eq.return_value.in_.assert_called_once_with(
            "trigger", ["issue_comment", "issue_label", "pull_request"]
        )
        # Assert that only completed requests are filtered
        mock_supabase.table.return_value.select.return_value.gt.return_value.eq.return_value.in_.return_value.eq.assert_called_once_with("is_completed", True)


if __name__ == "__main__":
    unittest.main()