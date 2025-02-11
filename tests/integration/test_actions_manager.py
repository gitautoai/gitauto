"""
Integration tests for services/github/actions_manager.py

This test verifies that get_workflow_run_path returns a valid GitHub API URL for checking workflow run jobs.
For more details, refer to https://docs.github.com/en/rest/actions/runs?apiVersion=2022-11-28
"""

from services.github.actions_manager import get_workflow_run_path
from tests.constants import OWNER, REPO, TOKEN


def test_get_workflow_run_path_format():
    """Test that get_workflow_run_path returns a URL containing the expected owner, repo, and run_id."""
    run_id = 1
    workflow_path = get_workflow_run_path(run_id, token=TOKEN, repo=REPO, owner=OWNER)
    expected_substr = f"/repos/{OWNER}/{REPO}/actions/runs/{run_id}/jobs"
    assert expected_substr in workflow_path, f"Expected '{expected_substr}' in output but got {workflow_path}"
