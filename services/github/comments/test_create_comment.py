import unittest
from unittest.mock import patch, MagicMock

from tests.constants import OWNER, REPO, TOKEN
from services.github.comments.create_comment import create_comment


class TestCreateComment(unittest.TestCase):
    def setUp(self):
        self.base_args = {
            "owner": OWNER,
            "repo": REPO,
            "token": TOKEN,
            "issue_number": 123
        }
        self.comment_body = "Test comment body"
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"url": "https://api.github.com/repos/owner/repo/issues/comments/1"}

    @patch("services.github.comments.create_comment.requests.post")
    def test_create_comment_github_success(self, mock_post):
        mock_post.return_value = self.mock_response
        
        result = create_comment(self.comment_body, self.base_args)
        
        mock_post.assert_called_once()
        self.mock_response.raise_for_status.assert_called_once()
        self.assertEqual(result, "https://api.github.com/repos/owner/repo/issues/comments/1")

    @patch("services.github.comments.create_comment.requests.post")
    def test_create_comment_github_with_explicit_input_from(self, mock_post):
        mock_post.return_value = self.mock_response
        base_args = self.base_args.copy()
        base_args["input_from"] = "github"
        
        result = create_comment(self.comment_body, base_args)
        
        mock_post.assert_called_once()
        self.mock_response.raise_for_status.assert_called_once()
        self.assertEqual(result, "https://api.github.com/repos/owner/repo/issues/comments/1")

    @patch("services.github.comments.create_comment.requests.post")
    def test_create_comment_github_http_error(self, mock_post):
        from requests.exceptions import HTTPError
        
        self.mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
        mock_post.return_value = self.mock_response
        
        result = create_comment(self.comment_body, self.base_args)
        
        mock_post.assert_called_once()
        self.mock_response.raise_for_status.assert_called_once()
        self.assertIsNone(result)  # Should return None due to @handle_exceptions

    @patch("services.github.comments.create_comment.requests.post")
    def test_create_comment_github_connection_error(self, mock_post):
        from requests.exceptions import ConnectionError
        
        mock_post.side_effect = ConnectionError("Connection refused")
        
        result = create_comment(self.comment_body, self.base_args)
        
        mock_post.assert_called_once()
        self.assertIsNone(result)  # Should return None due to @handle_exceptions

    @patch("services.github.comments.create_comment.requests.post")
    def test_create_comment_github_timeout_error(self, mock_post):
        from requests.exceptions import Timeout
        
        mock_post.side_effect = Timeout("Request timed out")
        
        result = create_comment(self.comment_body, self.base_args)
        
        mock_post.assert_called_once()
        self.assertIsNone(result)  # Should return None due to @handle_exceptions

    @patch("services.github.comments.create_comment.requests.post")
    def test_create_comment_github_json_error(self, mock_post):
        self.mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = self.mock_response
        
        result = create_comment(self.comment_body, self.base_args)
        
        mock_post.assert_called_once()
        self.mock_response.raise_for_status.assert_called_once()
        self.assertIsNone(result)  # Should return None due to @handle_exceptions

    def test_create_comment_jira(self):
        base_args = self.base_args.copy()
        base_args["input_from"] = "jira"
        
        result = create_comment(self.comment_body, base_args)
        
        self.assertIsNone(result)

    def test_create_comment_unknown_input_from(self):
        base_args = self.base_args.copy()
        base_args["input_from"] = "unknown"
        
        result = create_comment(self.comment_body, base_args)
        
        self.assertIsNone(result)  # Should return None as no condition matches


if __name__ == "__main__":
    unittest.main()