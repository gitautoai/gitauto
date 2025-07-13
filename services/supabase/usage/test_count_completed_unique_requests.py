# Standard imports
from datetime import datetime
from unittest.mock import Mock, patch

# Local imports
from services.supabase.usage.count_completed_unique_requests import count_completed_unique_requests


def test_count_completed_unique_requests_success():
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
    
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {
            "Organization/test-org/test-repo#1",
            "User/test-user/another-repo#2"
        }
        assert result == expected_unique_requests
        
        # Verify the query chain was called correctly
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once_with("owner_type, owner_name, repo_name, issue_number")
        mock_table.gt.assert_called_once_with("created_at", start_date)
        mock_table.eq.assert_called_with("installation_id", installation_id)
        mock_table.in_.assert_called_once_with(
            "trigger", ["issue_comment", "issue_label", "pull_request"]
        )


def test_count_completed_unique_requests_empty_result():
    """Test handling of empty result from database"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        assert result == set()


def test_count_completed_unique_requests_duplicate_records():
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
    
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert - should only contain unique requests
        expected_unique_requests = {
            "Organization/test-org/test-repo#1",
            "User/test-user/another-repo#2"
        }
        assert result == expected_unique_requests
        assert len(result) == 2  # Ensure duplicates are removed


def test_count_completed_unique_requests_different_issue_numbers():
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
    
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {
            "Organization/test-org/test-repo#1",
            "Organization/test-org/test-repo#2"
        }
        assert result == expected_unique_requests
        assert len(result) == 2


def test_count_completed_unique_requests_database_error():
    """Test error handling when database query fails"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert - should return default value (empty set) due to handle_exceptions decorator
        assert result == set()


def test_count_completed_unique_requests_with_special_characters():
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
    
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {
            "Organization/test-org-with-dashes/test.repo.with.dots#1",
            "User/test_user_with_underscores/repo-with-numbers-123#42"
        }
        assert result == expected_unique_requests


def test_count_completed_unique_requests_query_parameters():
    """Test that query parameters are passed correctly"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)
        
        installation_id = 98765
        start_date = datetime(2023, 6, 15, 10, 30, 45)
        
        # Execute
        count_completed_unique_requests(installation_id, start_date)
        
        # Assert that the correct parameters were used in the query
        mock_table.gt.assert_called_once_with("created_at", start_date)
        mock_table.eq.assert_called_with("installation_id", installation_id)


def test_count_completed_unique_requests_trigger_filter():
    """Test that the correct trigger types are filtered"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        count_completed_unique_requests(installation_id, start_date)
        
        # Assert that the correct trigger types are filtered
        mock_table.in_.assert_called_once_with(
            "trigger", ["issue_comment", "issue_label", "pull_request"]
        )


def test_count_completed_unique_requests_execute_exception():
    """Test error handling when execute method raises an exception"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")
        
        installation_id = 12345
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert - should return default value (empty set) due to handle_exceptions decorator
        assert result == set()


def test_count_completed_unique_requests_with_zero_values():
    """Test with zero values for installation_id"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "test-org",
            "repo_name": "test-repo",
            "issue_number": 1
        }
    ]
    
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)
        
        installation_id = 0
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {"Organization/test-org/test-repo#1"}
        assert result == expected_unique_requests
        mock_table.eq.assert_called_with("installation_id", 0)


def test_count_completed_unique_requests_with_large_values():
    """Test with large values for installation_id and issue_number"""
    mock_data = [
        {
            "owner_type": "User",
            "owner_name": "test-user",
            "repo_name": "test-repo",
            "issue_number": 999999999
        }
    ]
    
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)
        
        installation_id = 888888888
        start_date = datetime(2023, 1, 1)
        
        # Execute
        result = count_completed_unique_requests(installation_id, start_date)
        
        # Assert
        expected_unique_requests = {"User/test-user/test-repo#999999999"}
        assert result == expected_unique_requests
        mock_table.eq.assert_called_with("installation_id", 888888888)