import unittest
from unittest.mock import patch

from services.github.create_headers import create_headers


class TestCreateHeaders(unittest.TestCase):
    def test_create_headers_default_media_type(self):
        token = "dummy_token"
        with patch("services.github.create_headers.GITHUB_API_VERSION", "2022-11-28"), \
             patch("services.github.create_headers.GITHUB_APP_NAME", "dummy_app"):
            headers = create_headers(token)
            expected_accept = "application/vnd.github.v3+json"
            expected_auth = "Bearer dummy_token"
            expected_user_agent = "dummy_app"
            expected_api_version = "2022-11-28"
            self.assertEqual(headers["Accept"], expected_accept)
            self.assertEqual(headers["Authorization"], expected_auth)
            self.assertEqual(headers["User-Agent"], expected_user_agent)
            self.assertEqual(headers["X-GitHub-Api-Version"], expected_api_version)

    def test_create_headers_custom_media_type(self):
        token = "another_token"
        media_type = ".v4"
        with patch("services.github.create_headers.GITHUB_API_VERSION", "2022-11-28"), \
             patch("services.github.create_headers.GITHUB_APP_NAME", "dummy_app"):
            headers = create_headers(token, media_type)
            expected_accept = "application/vnd.github.v4+json"
            self.assertEqual(headers["Accept"], expected_accept)
            self.assertEqual(headers["Authorization"], "Bearer another_token")
            self.assertEqual(headers["User-Agent"], "dummy_app")
            self.assertEqual(headers["X-GitHub-Api-Version"], "2022-11-28")


if __name__ == '__main__':
    unittest.main()
