import unittest
from services.github.github_manager import get_user_locale

class TestGithubManager(unittest.TestCase):

    def test_get_user_locale_valid_user(self):
        # Assuming 'octocat' is a valid GitHub username for testing
        locale = get_user_locale('octocat')
        self.assertIsNotNone(locale)

    def test_get_user_locale_default_locale(self):
        # Testing with a hypothetical user with unknown locale
        locale = get_user_locale('unknown_user')
        self.assertEqual(locale, 'en-US')
