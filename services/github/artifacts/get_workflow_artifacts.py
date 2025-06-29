# Third-party libraries
from requests import get

# Internal libraries
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from services.github.types.artifact import Artifact
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_workflow_artifacts(owner: str, repo: str, run_id: int, token: str):
    """https://docs.github.com/en/rest/actions/artifacts?apiVersion=2022-11-28#list-workflow-run-artifacts"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
    headers = create_headers(token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    artifacts: list[Artifact] = response.json().get("artifacts", [])
    return artifacts
