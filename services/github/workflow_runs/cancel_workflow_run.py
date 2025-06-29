# Third party imports
from requests import post

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def cancel_workflow_run(owner: str, repo: str, run_id: int, token: str):
    """https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#cancel-a-workflow-run"""
    headers = create_headers(token=token, media_type="")
    cancel_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/cancel"
    post(url=cancel_url, headers=headers, timeout=TIMEOUT)
