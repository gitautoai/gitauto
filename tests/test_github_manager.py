import unittest
from services.github.github_manager import GitHubManager

class TestGitHubManager(unittest.TestCase):
    def setUp(self):
        self.github_manager = GitHubManager(token="your_test_token")

    def test_get_user_locale_success(self):
        locale = self.github_manager.get_user_locale("testuser")
        self.assertIsNotNone(locale)

    def test_get_user_locale_user_not_found(self):
        locale = self.github_manager.get_user_locale("nonexistentuser")
        self.assertEqual(locale, 'User not found')

    def test_get_user_locale_rate_limit_exceeded(self):
        locale = self.github_manager.get_user_locale("ratelimiteduser")
        self.assertEqual(locale, 'API rate limit exceeded')

    def test_get_user_locale_error(self):
        locale = self.github_manager.get_user_locale("erroruser")
        self.assertEqual(locale, 'Error retrieving locale')
# run this file locally with: python -m tests.test_github_manager
