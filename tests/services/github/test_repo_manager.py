import unittest
from unittest.mock import patch
from services.github.repo_manager import is_repo_forked


class TestRepoManager(unittest.TestCase):
    @patch('services.github.repo_manager.get')
    def test_is_repo_forked_true(self, mock_get):
        mock_get.return_value.json.return_value = {'fork': True}
        mock_get.return_value.raise_for_status = lambda: None
        self.assertTrue(is_repo_forked('owner', 'repo', 'token'))

    @patch('services.github.repo_manager.get')
    def test_is_repo_forked_false(self, mock_get):
        mock_get.return_value.json.return_value = {'fork': False}
        mock_get.return_value.raise_for_status = lambda: None
        self.assertFalse(is_repo_forked('owner', 'repo', 'token'))


if __name__ == '__main__':
    unittest.main()
