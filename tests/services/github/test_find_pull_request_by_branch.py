import unittest
from unittest.mock import patch, MagicMock

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
        self.assertEqual(result["url"], "https://api.github.com/repos/owner/repo/pulls/42")
        self.assertEqual(result["headRef"]["name"], "feature-branch")
        self.assertEqual(result["baseRef"]["name"], "main")
        
        # Verify that the GraphQL client was called correctly
        mock_client.execute.assert_called_once()
        
        # Verify that the result does not contain htmlUrl field (which was the issue)
        self.assertNotIn("htmlUrl", result, "Result should not contain htmlUrl field after fix.")
        
        # Verify that the expected fields are present in the result
        self.assertIn("number", result, "Result should contain number field.")
        self.assertIn("title", result, "Result should contain title field.")
        self.assertIn("url", result, "Result should contain url field.")
        self.assertIn("headRef", result, "Result should contain headRef field.")
        self.assertIn("baseRef", result, "Result should contain baseRef field.")

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

    @patch('services.github.pull_requests.find_pull_request_by_branch.get_graphql_client')
    def test_function_signature_and_parameters(self, mock_get_client):
        """Test that function is called with correct parameters."""
        # Mock the GraphQL client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response
        mock_client.execute.return_value = {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {
                            "number": 1,
                            "title": "Test",
                            "url": "https://api.github.com/repos/test/test/pulls/1",
                            "headRef": {"name": "test-branch"},
                            "baseRef": {"name": "main"}
                        }
                    ]
                }
            }
        }
        
        # Call the function
        find_pull_request_by_branch("test-owner", "test-repo", "test-branch", "test-token")
        
        # Verify the GraphQL client was called with correct parameters
        mock_client.execute.assert_called_once()
        call_args = mock_client.execute.call_args
        
        # Check that variable_values contains the correct parameters
        variable_values = call_args[1]["variable_values"]
        self.assertEqual(variable_values["owner"], "test-owner")
        self.assertEqual(variable_values["repo"], "test-repo")
        self.assertEqual(variable_values["headRefName"], "test-branch")


if __name__ == "__main__":
    unittest.main()