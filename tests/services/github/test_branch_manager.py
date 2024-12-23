import unittest
from unittest.mock import patch
from services.github.branch_manager import get_default_branch
from tests.constants import GITHUB_OWNER, GITHUB_REPO, TEST_TOKEN, DEFAULT_BRANCH


class TestBranchManager(unittest.TestCase):
    @patch('services.github.branch_manager.requests.get')
    def test_get_default_branch(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{
            "name": DEFAULT_BRANCH,
            "commit": {"sha": "test_sha"}
        }]

        branch_name, commit_sha = get_default_branch(GITHUB_OWNER, GITHUB_REPO, TEST_TOKEN)

        self.assertEqual(branch_name, DEFAULT_BRANCH)
        self.assertEqual(commit_sha, "test_sha")

if __name__ == '__main__':
    unittest.main()
