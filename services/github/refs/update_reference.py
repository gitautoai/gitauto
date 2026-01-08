import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def update_reference(base_args: BaseArgs, new_commit_sha: str):
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    branch = base_args["new_branch"]

    # https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#update-a-reference
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs/heads/{branch}"
    headers = create_headers(token=token)
    data = {"sha": new_commit_sha}

    response = requests.patch(url=url, json=data, headers=headers, timeout=TIMEOUT)

    print(
        f"update_reference: owner={owner}, repo={repo}, branch={branch}, new_commit_sha={new_commit_sha}, status={response.status_code}"
    )

    response.raise_for_status()
