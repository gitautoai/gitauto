# Standard imports
import base64
import os
from typing import cast

# Third party imports
from anthropic.types import ToolUnionParam
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.claude.tools.file_modify_result import FileWriteResult
from services.claude.tools.properties import FILE_PATH
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.new_lines.detect_new_line import detect_line_break
from utils.text.ensure_final_newline import ensure_final_newline
from utils.text.sort_imports import sort_imports
from utils.text.strip_trailing_spaces import strip_trailing_spaces

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
REPLACE_REMOTE_FILE_CONTENT: ToolUnionParam = {
    "name": "replace_remote_file_content",
    "description": "Replaces the entire content of a file in the local clone and commits the change to the PR branch. Use this when the entire file or many lines need to be rewritten. For minor modifications, use apply_diff_to_file instead.",
    "input_schema": {
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


@handle_exceptions(
    default_return_value=lambda file_content, file_path, base_args, **kwargs: FileWriteResult(
        success=False,
        message="Unexpected error occurred.",
        file_path=file_path,
        content="",
    ),
    raise_on_error=False,
)
def replace_remote_file_content(
    file_content: str,
    file_path: str,
    base_args: BaseArgs,
    commit_message: str | None = None,
    **_kwargs,
):
    """Replace the content of a remote file directly without using unified diff and patch commands."""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]
    skip_ci = base_args.get("skip_ci", False)

    # https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)

    # Get the current file to retrieve its SHA (Secure Hash Algorithm)
    get_response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # Sort imports, strip trailing spaces, and ensure final newline
    file_content = sort_imports(file_content, file_path)
    file_content = strip_trailing_spaces(file_content)
    file_content = ensure_final_newline(file_content)

    # Set up the data for the PUT request
    message = commit_message if commit_message else f"Replace content of {file_path}"
    message = f"{message} [skip ci]" if skip_ci else message
    content = base64.b64encode(file_content.encode(UTF8)).decode(UTF8)
    data = {"message": message, "content": content, "branch": new_branch}

    # Add SHA if the file exists
    if get_response.status_code != 404:
        get_response.raise_for_status()
        file_info = get_response.json()

        # Check if the response is a file (not a directory)
        if isinstance(file_info, list):
            return FileWriteResult(
                success=False,
                message=f"'{file_path}' returned multiple files. Specify a single file path.",
                file_path=file_path,
                content="",
            )

        if file_info.get("type") == "dir":
            return FileWriteResult(
                success=False,
                message=f"'{file_path}' is a directory, not a file.",
                file_path=file_path,
                content="",
            )

        # Claude's JSON output always uses LF. Convert file_content to match the original line endings BEFORE comparison so both the skip check and the upload use the correct line endings.
        existing_content = base64.b64decode(file_info.get("content", "")).decode(UTF8)
        original_line_break = detect_line_break(text=existing_content)
        if original_line_break != "\n":
            file_content = file_content.replace("\n", original_line_break)
            content = base64.b64encode(file_content.encode(UTF8)).decode(UTF8)
            data["content"] = content

        if existing_content == file_content:
            logger.info("No changes to %s, skipping", file_path)
            return FileWriteResult(
                success=True,
                message=f"No changes to {file_path}.",
                file_path=file_path,
                content=file_content,
            )

        # Add SHA to the request data
        data["sha"] = file_info.get("sha", "")

    # Replace the content of the remote file
    put_response = requests.put(url=url, json=data, headers=headers, timeout=TIMEOUT)
    put_response.raise_for_status()
    commit_sha = cast(str, put_response.json()["commit"]["sha"])

    # Also create or overwrite local file for verification (tsc, jest, eslint, etc.)
    clone_dir = base_args["clone_dir"]
    local_path = os.path.join(clone_dir, file_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding=UTF8) as f:
        f.write(file_content)
    logger.info("Wrote to local (changed): %s", local_path)

    return FileWriteResult(
        success=True,
        message=f"Replaced {file_path}.",
        file_path=file_path,
        content=file_content,
        commit_sha=commit_sha,
    )
