import unittest
from unittest.mock import patch
from services.github.branch_manager import get_default_branch
from tests.constants import GITHUB_API_URL, OWNER, REPO, TOKEN


def test_get_default_branch_success():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                "name": "main",
                "commit": {"sha": "abc123"}
            }
        ]
        default_branch, commit_sha = get_default_branch(OWNER, REPO, TOKEN)
        assert default_branch == "main"
        assert commit_sha == "abc123"


def test_get_default_branch_failure():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
        default_branch, commit_sha = get_default_branch(OWNER, REPO, TOKEN)
        assert default_branch == "main"
        assert commit_sha == ""


if __name__ == "__main__":
    unittest.main()
