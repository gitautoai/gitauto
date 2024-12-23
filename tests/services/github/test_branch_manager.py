import pytest
import requests_mock
from services.github.branch_manager import get_default_branch
from tests.constants import GITHUB_API_URL, OWNER, REPO, TOKEN


def test_get_default_branch_success(requests_mock):
    url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/branches"
    mock_response = [
        {
            "name": "main",
            "commit": {
                "sha": "abc123"
            }
        }
    ]
    requests_mock.get(url, json=mock_response)

    default_branch_name, latest_commit_sha = get_default_branch(OWNER, REPO, TOKEN)

    assert default_branch_name == "main"
    assert latest_commit_sha == "abc123"


def test_get_default_branch_failure(requests_mock):
    url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/branches"
    requests_mock.get(url, status_code=404)

    default_branch_name, latest_commit_sha = get_default_branch(OWNER, REPO, TOKEN)
    assert default_branch_name == "main"  # default return value on error
