# pyright: reportUnusedVariable=false
# pylint: disable=unused-argument
from unittest.mock import patch

import pytest

from services.website.retarget_pr import retarget_pr

MODULE = "services.website.retarget_pr"


@pytest.fixture
def mock_get_clone_url():
    with patch(f"{MODULE}.get_clone_url") as mock:
        mock.return_value = "https://x-access-token:fake@github.com/owner/repo.git"
        yield mock


@pytest.fixture
def mock_get_clone_dir():
    with patch(f"{MODULE}.get_clone_dir") as mock:
        mock.return_value = "/tmp/owner/repo/pr-42"
        yield mock


@pytest.fixture
def mock_get_pull_request():
    with patch(f"{MODULE}.get_pull_request") as mock:
        mock.return_value = {
            "head": {"ref": "gitauto/issue-42"},
            "base": {
                "repo": {
                    "id": 999,
                    "fork": False,
                    "owner": {"id": 100, "type": "Organization"},
                },
            },
            "title": "Add feature X",
            "body": "Closes #42",
            "user": {"login": "gitauto-ai[bot]"},
        }
        yield mock


@pytest.fixture
def mock_git_clone_to_tmp():
    with patch(f"{MODULE}.git_clone_to_tmp") as mock:
        yield mock


@pytest.fixture
def mock_reset_pr_branch_to_new_base():
    with patch(f"{MODULE}.reset_pr_branch_to_new_base") as mock:
        mock.return_value = "Reset 3 files onto develop."
        yield mock


def test_retarget_pr_clones_and_delegates(
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_get_pull_request,
    mock_git_clone_to_tmp,
    mock_reset_pr_branch_to_new_base,
):
    retarget_pr(
        owner_name="owner",
        repo_name="repo",
        token="fake-token",
        new_base_branch="develop",
        pr_number=42,
        installation_id=12345,
    )
    mock_get_pull_request.assert_called_once()
    mock_git_clone_to_tmp.assert_called_once_with(
        clone_dir="/tmp/owner/repo/pr-42",
        clone_url="https://x-access-token:fake@github.com/owner/repo.git",
        branch="gitauto/issue-42",
    )
    mock_reset_pr_branch_to_new_base.assert_called_once()
    call_kwargs = mock_reset_pr_branch_to_new_base.call_args[1]
    assert call_kwargs["new_base_branch"] == "develop"
    assert call_kwargs["base_args"]["owner"] == "owner"
    assert call_kwargs["base_args"]["repo"] == "repo"
    assert call_kwargs["base_args"]["pr_number"] == 42
    assert call_kwargs["base_args"]["platform"] == "github"
    # retarget_pr has no LLM calls, so it passes usage_id=0 as a placeholder — no llm_requests row is ever written from this path.
    assert call_kwargs["base_args"]["usage_id"] == 0
