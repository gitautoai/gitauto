import json
import requests

from services.github.commits.get_commit_diff import get_commit_diff


class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


def dummy_get(url, headers, timeout):
    commit_data = {
        "commit": {
            "message": "Test commit message",
            "author": {"name": "Test Author", "email": "author@test.com"}
        },
        "files": [
            {
                "filename": "example.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15,
                "patch": "dummy diff content"
            }
        ]
    }
    return DummyResponse(commit_data)


def test_get_commit_diff_success(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_get)
    token = "dummy_token"
    owner = "dummy_owner"
    repo = "dummy_repo"
    commit_sha = "abc123"

    result = get_commit_diff(owner, repo, commit_sha, token)
    assert result is not None
    assert result["commit_id"] == commit_sha
    assert result["message"] == "Test commit message"
    assert result["author"]["name"] == "Test Author"
    assert len(result["files"]) == 1
    file_info = result["files"][0]
    assert file_info["filename"] == "example.py"
    assert file_info["status"] == "modified"


def dummy_get_failure(url, headers, timeout):
    response = type("DummyResponse", (), {"status_code": 404})()
    raise requests.HTTPError("Dummy error", response=response)


def test_get_commit_diff_failure(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_get_failure)
    token = "dummy_token"
    owner = "dummy_owner"
    repo = "dummy_repo"
    commit_sha = "abc123"

    result = get_commit_diff(owner, repo, commit_sha, token)
    assert result is None
