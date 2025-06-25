import unittest
from unittest.mock import patch, MagicMock, call

from services.github.pull_requests.find_pull_request_by_branch import find_pull_request_by_branch


class TestFindPullRequestByBranch(unittest.TestCase):
    @patch('services.github.pull_requests.find_pull_request_by_branch.gql')
    @patch('services.github.pull_requests.find_pull_request_by_branch.get_graphql_client')
    def test_removed_htmlUrl(self, mock_get_client, mock_gql):
        """Test that the GraphQL query does not contain htmlUrl field."""
        # Mock the GraphQL client and its execute method
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Make gql function pass through the query string for testing
        mock_gql.side_effect = lambda query: query
        
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
        
        # Get the query string that was passed to gql
        mock_gql.assert_called_once()
        query_string = mock_gql.call_args[0][0]
        
        # Ensure the query does not contain 'htmlUrl'
        self.assertNotIn("htmlUrl", query_string, "Query should not contain htmlUrl field after fix.")
        
        # Additionally, check that other expected fields are present in the query
        self.assertIn("number", query_string, "Query should contain number field.")
        self.assertIn("title", query_string, "Query should contain title field.")
        self.assertIn("url", query_string, "Query should contain url field.")
        self.assertIn("headRef", query_string, "Query should contain headRef field.")
        self.assertIn("baseRef", query_string, "Query should contain baseRef field.")

    @patch('services.github.pull_requests.find_pull_request_by_branch.gql')
    @patch('services.github.pull_requests.find_pull_request_by_branch.get_graphql_client')
    def test_no_pull_request_found(self, mock_get_client, mock_gql):
        """Test that function returns None when no pull request is found."""
        # Mock the GraphQL client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Make gql function pass through the query string
        mock_gql.side_effect = lambda query: query
        
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

    @patch('services.github.pull_requests.find_pull_request_by_branch.gql')
    @patch('services.github.pull_requests.find_pull_request_by_branch.get_graphql_client')
    def test_graphql_error_handling(self, mock_get_client, mock_gql):
        """Test that function handles GraphQL errors gracefully."""
        # Mock the GraphQL client to raise an exception
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Make gql function pass through the query string
        mock_gql.side_effect = lambda query: query
        mock_client.execute.side_effect = Exception("GraphQL error")
        
        # Call the function - should not raise exception due to @handle_exceptions decorator
        result = find_pull_request_by_branch("owner", "repo", "feature-branch", "token")
        
        # Verify None is returned on error
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()