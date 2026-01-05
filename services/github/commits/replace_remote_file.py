# Standard imports
import base64

# Third party imports
from openai.types import shared_params
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.eslint.run_eslint import run_eslint
from services.github.files.get_eslint_config import get_eslint_config
from services.github.files.get_raw_content import get_raw_content
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from services.openai.functions.properties import FILE_PATH
from utils.error.handle_exceptions import handle_exceptions
from utils.text.strip_trailing_spaces import strip_trailing_spaces
from utils.text.ensure_final_newline import ensure_final_newline
from utils.text.sort_imports import sort_imports

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
    skip_ci = base_args.get("skip_ci", False)

    # Prepare the request
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)

    # Get the current file to retrieve its SHA (Secure Hash Algorithm)
    get_response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # Sort imports, strip trailing spaces, and ensure final newline
    file_content = sort_imports(file_content, file_path)
    file_content = strip_trailing_spaces(file_content)
    file_content = ensure_final_newline(file_content)

    if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        eslint_config = get_eslint_config(base_args)
        if eslint_config:
            package_json_content = get_raw_content(
                owner=owner,
                repo=repo,
                file_path="package.json",
                ref=new_branch,
                token=token,
            )
            eslint_result = run_eslint(
                owner=owner,
                repo=repo,
                file_path=file_path,
                file_content=file_content,
                eslint_config_content=eslint_config["content"],
                package_json_content=package_json_content,
            )
            if eslint_result and eslint_result["fixed_content"]:
                file_content = eslint_result["fixed_content"]
        else:
            print(
                f"No ESLint config found for {owner}/{repo}, skipping ESLint validation"
            )

    # Set up the data for the PUT request
    message = (
        f"Replace content of {file_path} [skip ci]"
        if skip_ci
        else f"Replace content of {file_path}"
    )
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
