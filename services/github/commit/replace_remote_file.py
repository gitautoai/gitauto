# Standard imports
import base64

# Third party imports
from openai.types import shared_params
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.github.create_headers import create_headers
from services.github.github_types import BaseArgs
from services.openai.functions.properties import FILE_PATH
from utils.error.handle_exceptions import handle_exceptions

# Define the function for replacing remote file content
REPLACE_REMOTE_FILE_CONTENT: shared_params.FunctionDefinition = {
    "name": "replace_remote_file_content",
    "description": "Replaces the content of a remote file directly in the GitHub repository. This function is ideal for scenarios where the entire file or many lines need to be rewritten, such as converting a class-based file to a function-based one or making comprehensive updates. Using a unified diff format for such extensive changes can be inefficient, as it requires specifying changes for each line, resulting in a diff size that is twice the number of lines in the file. In contrast, this function allows you to provide the complete updated content, which is more efficient for large-scale changes. For minor modifications, where only a small part of the file needs to be changed, using a diff-based approach is more appropriate.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
            "file_content": {
                "type": "string",
                "description": "The new content to replace the existing file content with.",
            },
        },
        "required": ["file_path", "file_content"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def replace_remote_file_content(
    file_content: str,
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Replace the content of a remote file directly without using unified diff and patch commands."""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]

    # Prepare the request
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)

    # Get the current file to retrieve its SHA (Secure Hash Algorithm)
    get_response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # Set up the data for the PUT request
    message = f"Replace content of {file_path}"
    content = base64.b64encode(file_content.encode(UTF8)).decode(UTF8)
    data = {"message": message, "content": content, "branch": new_branch}

    # Add SHA if the file exists
    if get_response.status_code != 404:
        get_response.raise_for_status()
        file_info = get_response.json()

        # Check if the response is a file (not a directory)
        if isinstance(file_info, list):
            return f"file_path: '{file_path}' returned multiple files. Please specify a single file path."

        if file_info.get("type") == "dir":
            return f"file_path: '{file_path}' is a directory. It should be a file path."

        # Add SHA to the request data
        data["sha"] = file_info.get("sha", "")

    # Replace the content of the remote file
    put_response = requests.put(url=url, json=data, headers=headers, timeout=TIMEOUT)
    put_response.raise_for_status()
    return f"Content replaced in the file: {file_path} successfully."
