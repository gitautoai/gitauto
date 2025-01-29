@@ -0,0 +1,25 @@
import pytest
from unittest.mock import patch, MagicMock
from services.github.repo_manager import is_repo_forked

@patch("requests.get")
def test_is_repo_forked_true(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"fork": True}

    owner = "test_owner"
    repo = "test_repo"
    token = "test_token"
    assert is_repo_forked(owner, repo, token) == True, "Should return True if repository is a fork"

@patch("requests.get")
def test_is_repo_forked_false(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"fork": False}

    owner = "test_owner"
    repo = "test_repo"
    token = "test_token"
    assert is_repo_forked(owner, repo, token) == False, "Should return False if repository is not a fork"
```
