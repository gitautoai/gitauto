# Standard imports
from typing import Literal, TypedDict

# Third party imports
import requests

# Local imports
from config import PER_PAGE, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


Status = Literal["added", "modified", "removed"]


class FileChange(TypedDict):
    filename: str
    status: Status


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_pull_request_files(url: str, token: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files"""
    headers = create_headers(token=token)
    file_changes: list[FileChange] = []
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
            if "filename" in file and "status" in file:
                file_changes.append(
                    {"filename": file["filename"], "status": file["status"]}
                )

        page += 1

    return file_changes
