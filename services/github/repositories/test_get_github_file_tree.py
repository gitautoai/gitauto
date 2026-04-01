# pyright: reportUnusedVariable=false
from unittest.mock import MagicMock, patch

from services.github.repositories.get_github_file_tree import get_github_file_tree

MODULE = "services.github.repositories.get_github_file_tree"

GITHUB_TREE_RESPONSE = {
    "sha": "abc123",
    "truncated": False,
    "tree": [
        {
            "path": "src/main.py",
            "mode": "100644",
            "type": "blob",
            "sha": "a1",
            "size": 1234,
        },
        {
            "path": "src/utils.py",
            "mode": "100644",
            "type": "blob",
            "sha": "b2",
            "size": 567,
        },
        {"path": "src/tests", "mode": "040000", "type": "tree", "sha": "c3"},
    ],
}


class TestGetGithubFileTree:
    @patch(f"{MODULE}.requests.get")
    def test_returns_tree_items(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = GITHUB_TREE_RESPONSE
        mock_get.return_value = mock_response

        items = get_github_file_tree("owner", "repo", "main", "token")

        assert len(items) == 3
        assert items[0]["path"] == "src/main.py"
        assert items[0]["type"] == "blob"
        assert items[0].get("size") == 1234
        assert items[1]["path"] == "src/utils.py"
        assert items[2]["path"] == "src/tests"
        assert items[2]["type"] == "tree"
        assert "size" not in items[2]

    @patch(f"{MODULE}.requests.get")
    def test_returns_empty_list_on_api_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        items = get_github_file_tree("owner", "repo", "main", "token")

        assert not items
        assert isinstance(items, list)

    @patch(f"{MODULE}.requests.get")
    def test_returns_empty_list_when_tree_is_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sha": "abc", "truncated": False, "tree": []}
        mock_get.return_value = mock_response

        items = get_github_file_tree("owner", "repo", "main", "token")

        assert not items

    @patch(f"{MODULE}.requests.get")
    def test_calls_correct_api_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sha": "abc", "truncated": False, "tree": []}
        mock_get.return_value = mock_response

        get_github_file_tree("myowner", "myrepo", "feature-branch", "mytoken")

        called_url = mock_get.call_args[0][0]
        assert (
            called_url
            == "https://api.github.com/repos/myowner/myrepo/git/trees/feature-branch?recursive=1"
        )
        assert mock_get.call_args[1]["headers"]["Authorization"] == "token mytoken"

    @patch(f"{MODULE}.requests.get")
    def test_handles_truncated_tree(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sha": "abc",
            "truncated": True,
            "tree": [
                {
                    "path": "file.py",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "d4",
                    "size": 100,
                },
            ],
        }
        mock_get.return_value = mock_response

        items = get_github_file_tree("owner", "repo", "main", "token")

        # Should still return items even when truncated
        assert len(items) == 1
        assert items[0]["path"] == "file.py"
