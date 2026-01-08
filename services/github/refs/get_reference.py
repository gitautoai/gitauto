from typing import cast

import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_reference(base_args: BaseArgs):
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    branch = base_args["new_branch"]

    # https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#get-a-reference
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{branch}"
    headers = create_headers(token=token)

    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return cast(str, response.json()["object"]["sha"])
