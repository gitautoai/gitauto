import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def create_remote_branch(sha: str, base_args: BaseArgs) -> None:
    owner = base_args["owner"]
    repo = base_args["repo"]
    branch_name = base_args["new_branch"]
    token = base_args["token"]
    response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs",
        headers=create_headers(token=token),
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
