# Third party imports
from typing import cast
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.workflow_run import WorkflowRun
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_workflow_runs(
    owner: str,
    repo: str,
    token: str,
    commit_sha: str | None = None,
    branch: str | None = None,
    per_page: int = 30,
    max_pages: int = 1,
):
    # https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository
    if not commit_sha and not branch:
        raise ValueError("Either commit_sha or branch must be provided")

    headers = create_headers(token=token, media_type="")
    all_runs: list[WorkflowRun] = []

    for page in range(1, max_pages + 1):
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs?per_page={per_page}&page={page}"
        if commit_sha:
            url += f"&head_sha={commit_sha}"
        else:
            url += f"&branch={branch}"

        response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()

        runs = response.json().get("workflow_runs", [])
        all_runs.extend(cast(list[WorkflowRun], runs))

        if len(runs) < per_page:
            break

    return all_runs
