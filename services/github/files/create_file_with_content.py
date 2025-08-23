# Standard imports
import base64

# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_file_with_content(
    file_path: str,
    content: str,
    base_args: BaseArgs,
    commit_message: str = None,
    **_kwargs,
):
    """Create a new file in GitHub repository with the given content."""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]
    skip_ci = base_args.get("skip_ci", False)

    # Use custom message or default
    if commit_message is None:
        commit_message = (
            f"Create {file_path} [skip ci]" if skip_ci else f"Create {file_path}"
        )

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)

    # Encode content to base64
    encoded_content = base64.b64encode(content.encode(UTF8)).decode(UTF8)

    create_data = {
        "message": commit_message,
        "content": encoded_content,
        "branch": new_branch,
    }

    response = requests.put(url=url, json=create_data, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    return f"File {file_path} successfully created"
