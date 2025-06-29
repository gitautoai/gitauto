# Third party imports
from requests import get, post

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def cancel_workflow_run(owner: str, repo: str, commit_sha: str, token: str) -> None:
    """https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs?head_sha={commit_sha}"
    headers = create_headers(token=token, media_type="")

    response = get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    workflow_runs = response.json()["workflow_runs"]
    statuses_to_cancel = ["queued", "in_progress", "pending", "waiting", "requested"]
    for run in workflow_runs:
        run_name = run["name"]
        run_status = run["status"]
        print(f"Cancelling {run_name} with status {run_status} in {owner}/{repo}")
        if run_status in statuses_to_cancel:
            # https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#cancel-a-workflow-run
            cancel_url = (
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs/{run['id']}/cancel"
            )
            post(url=cancel_url, headers=headers, timeout=TIMEOUT)
