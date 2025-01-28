import unittest
from unittest.mock import patch
from services.github.repo_manager import is_repo_forked


class TestRepoManager(unittest.TestCase):
    @patch('services.github.repo_manager.get')
    def test_is_repo_forked(self, mock_get):
        # Mock response for a forked repository
        mock_get.return_value.json.return_value = {'fork': True}
        mock_get.return_value.raise_for_status = lambda: None
        self.assertTrue(is_repo_forked('owner', 'repo', 'token'))

        # Mock response for a non-forked repository
        mock_get.return_value.json.return_value = {'fork': False}
        self.assertFalse(is_repo_forked('owner', 'repo', 'token'))


if __name__ == '__main__':
    unittest.main()
# run this file locally with: python -m tests.test_github_manager
