# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_file_by_sha(
    file_path: str,
    sha: str,
    base_args: BaseArgs,
    commit_message: str | None = None,
    **_kwargs,
):
    """Delete a file from GitHub repository using its SHA."""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]
    skip_ci = base_args.get("skip_ci", False)

    # Use custom message or default
    if commit_message is None:
        commit_message = (
            f"Delete {file_path} [skip ci]" if skip_ci else f"Delete {file_path}"
        )

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)

    delete_data = {
        "message": commit_message,
        "sha": sha,
        "branch": new_branch,
    }

    response = requests.delete(
        url=url, json=delete_data, headers=headers, timeout=TIMEOUT
    )
    response.raise_for_status()

    return f"File {file_path} successfully deleted"
