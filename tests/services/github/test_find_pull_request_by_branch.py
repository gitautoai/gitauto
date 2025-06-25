import unittest
from unittest.mock import patch, MagicMock, call

from services.github.pull_requests.find_pull_request_by_branch import find_pull_request_by_branch


class TestFindPullRequestByBranch(unittest.TestCase):
    @patch('services.github.pull_requests.find_pull_request_by_branch.get_graphql_client')
    def test_removed_htmlUrl(self, mock_get_client):
        """Test that the GraphQL query does not contain htmlUrl field."""
        # Mock the GraphQL client and its execute method
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the response to return a valid pull request
        mock_client.execute.return_value = {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {
                            "number": 42,
                            "title": "Test PR",
                            "url": "https://api.github.com/repos/owner/repo/pulls/42",
                            "headRef": {"name": "feature-branch"},
                            "baseRef": {"name": "main"}
                        }
                    ]
                }
            }
        }
        
        # Call the function with proper arguments
        result = find_pull_request_by_branch("owner", "repo", "feature-branch", "token")
        
        # Verify the function was called and returned expected result
        self.assertIsNotNone(result)
        self.assertEqual(result["number"], 42)
        self.assertEqual(result["title"], "Test PR")
        
        # Verify that client.execute was called
        mock_client.execute.assert_called_once()
        
        # Get the query that was executed - it should be a DocumentNode
        query_call = mock_client.execute.call_args[0][0]
        
        # Convert the DocumentNode to string to check its content
        # The DocumentNode should have a loc.source.body attribute containing the query string
        if hasattr(query_call, 'loc') and hasattr(query_call.loc, 'source'):
            query_string = query_call.loc.source.body
        else:
            # Fallback: try to get string representation
            query_string = str(query_call)
        
        # Ensure the query does not contain 'htmlUrl'
        self.assertNotIn("htmlUrl", query_string, "Query should not contain htmlUrl field after fix.")
        
        # Additionally, check that other expected fields are present in the query
        self.assertIn("number", query_string, "Query should contain number field.")
        self.assertIn("title", query_string, "Query should contain title field.")
        self.assertIn("url", query_string, "Query should contain url field.")
        self.assertIn("headRef", query_string, "Query should contain headRef field.")
        self.assertIn("baseRef", query_string, "Query should contain baseRef field.")

    @patch('services.github.pull_requests.find_pull_request_by_branch.get_graphql_client')
    def test_no_pull_request_found(self, mock_get_client):
        """Test that function returns None when no pull request is found."""
        # Mock the GraphQL client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock empty response
        mock_client.execute.return_value = {
            "repository": {
                "pullRequests": {
                    "nodes": []
                }
            }
        }
        
        # Call the function
        result = find_pull_request_by_branch("owner", "repo", "nonexistent-branch", "token")
        
        # Verify None is returned when no PR is found
        self.assertIsNone(result)

    @patch('services.github.pull_requests.find_pull_request_by_branch.get_graphql_client')
    def test_graphql_error_handling(self, mock_get_client):
        """Test that function handles GraphQL errors gracefully."""
        # Mock the GraphQL client to raise an exception
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.execute.side_effect = Exception("GraphQL error")
        
        # Call the function - should not raise exception due to @handle_exceptions decorator
        result = find_pull_request_by_branch("owner", "repo", "feature-branch", "token")
        
        # Verify None is returned on error
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()