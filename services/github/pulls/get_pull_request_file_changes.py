import requests
from config import TIMEOUT, PER_PAGE
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_pull_request_file_changes(url: str, token: str):
    """url: https://api.github.com/repos/gitautoai/gitauto/pulls/517/files is expected.
    https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files
    """
    headers = create_headers(token=token)
    changes: list[dict[str, str]] = []
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
            if "patch" not in file:
                continue
            filename, status, patch = file["filename"], file["status"], file["patch"]
            changes.append({"filename": filename, "status": status, "patch": patch})
        page += 1
    return changes
