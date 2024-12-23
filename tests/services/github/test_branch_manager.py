import unittest
from unittest.mock import patch
from services.github.branch_manager import get_default_branch


class TestBranchManager(unittest.TestCase):

    @patch('services.github.branch_manager.requests.get')
    def test_get_default_branch(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{
            "name": "main",
            "commit": {"sha": "abc123"}
        }]

        default_branch, commit_sha = get_default_branch("owner", "repo", "token")
        self.assertEqual(default_branch, "main")
        self.assertEqual(commit_sha, "abc123")

if __name__ == '__main__':
    unittest.main()
