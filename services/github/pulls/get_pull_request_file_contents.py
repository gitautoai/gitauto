from json import dumps
import requests
from config import TIMEOUT, PER_PAGE
from services.github.files.get_remote_file_content import get_remote_file_content
from services.github.utils.create_headers import create_headers
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_pull_request_file_contents(url: str, base_args: BaseArgs):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files"""
    token = base_args["token"]
    headers = create_headers(token=token)
    contents: list[str] = []
    page = 1
    while True:
        params = {"per_page": PER_PAGE, "page": page}
        response = requests.get(
            url=url, headers=headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        files = response.json()
        if not files:
            break
        for file in files:
            file_path = file["filename"]
            content = get_remote_file_content(file_path=file_path, base_args=base_args)
            contents.append(content)
        page += 1

    print(f"get_pull_request_file_contents: {dumps(obj=contents, indent=2)}")
    return contents
