# Standard imports
import base64

# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.claude.tools.file_modify_result import FileWriteResult
from services.github.commits.format_commit_message import format_commit_message
from services.github.files.delete_remote_file import delete_remote_file
from services.github.types.contents import Contents
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.files.apply_patch import apply_patch
from utils.logging.logging_config import logger


@handle_exceptions(
    default_return_value=lambda diff, file_path, base_args, **kwargs: FileWriteResult(
        success=False,
        message="Unexpected error occurred.",
        file_path=file_path,
        content="",
    ),
    raise_on_error=False,
)
def apply_diff_to_file(
    diff: str,
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents"""
    skip_ci = base_args.get("skip_ci", False)
    message = f"Update {file_path} [skip ci]" if skip_ci else f"Update {file_path}"
    message = format_commit_message(message=message, base_args=base_args)
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    new_branch = base_args["new_branch"]
    if not new_branch:
        raise ValueError("new_branch is not set.")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)
    get_response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # If 404 error, the file doesn't exist.
    if get_response.status_code == 404:
        original_text, sha = "", ""
    else:
        get_response.raise_for_status()
        file_info: Contents = get_response.json()

        # Handle case where response is a list (directory listing) instead of a single file
        if isinstance(file_info, list):
            return FileWriteResult(
                success=False,
                message=f"'{file_path}' returned multiple files. Specify a single file path.",
                file_path=file_path,
                content="",
            )

        # Return if the file_path is a directory. See Example2 at https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
        if file_info.get("type") == "dir":
            return FileWriteResult(
                success=False,
                message=f"'{file_path}' is a directory, not a file.",
                file_path=file_path,
                content="",
            )

        # Get the original text and SHA of the file
        s1: str = file_info.get("content", "")
        # content is base64 encoded by default in GitHub API
        original_text = base64.b64decode(s=s1).decode(encoding=UTF8, errors="replace")
        sha: str = file_info.get("sha", "")

    # Apply the diff locally
    clone_dir = base_args["clone_dir"]
    result = apply_patch(
        original_text=original_text,
        diff_text=diff,
        clone_dir=clone_dir,
        file_path=file_path,
    )

    if result.error:
        return FileWriteResult(
            success=False,
            message=result.error,
            file_path=file_path,
            content=original_text,
        )

    # Handle file deletion
    if result.content == "" and "+++ /dev/null" in diff:
        delete_remote_file(file_path, sha, base_args)
        return FileWriteResult(
            success=True,
            message=f"Deleted {file_path}.",
            file_path=file_path,
            content="",
        )

    # Skip if content is identical (avoids empty commits and misleading logs)
    if result.content == original_text:
        logger.info("No changes to %s, skipping", file_path)
        return FileWriteResult(
            success=True,
            message=f"No changes to {file_path}.",
            file_path=file_path,
            content=result.content,
        )

    # Normal file update
    s2 = result.content.encode(encoding=UTF8)
    data = {
        "message": message,
        "content": base64.b64encode(s=s2).decode(encoding=UTF8),
        "branch": new_branch,
    }
    if sha != "":
        data["sha"] = sha

    # Create, update, or delete the file
    put_response = requests.put(
        url=url,
        json=data,
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    put_response.raise_for_status()

    return FileWriteResult(
        success=True,
        message=f"Applied diff to {file_path}.",
        file_path=file_path,
        content=result.content,
    )
