# Third party imports
from typing import cast
from requests import get

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
):
    if (not commit_sha or commit_sha == "") and (not branch or branch == ""):
        return []

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs"
    if commit_sha:
        url += f"?head_sha={commit_sha}"
    else:  # branch
        url += f"?branch={branch}"

    headers = create_headers(token=token, media_type="")
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    return cast(list[WorkflowRun], response.json()["workflow_runs"])
