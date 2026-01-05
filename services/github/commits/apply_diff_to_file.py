# Third party imports
import base64
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.eslint.run_eslint import run_eslint
from services.github.files.get_eslint_config import get_eslint_config
from services.github.files.get_raw_content import get_raw_content
from services.github.types.contents import Contents
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.files.apply_patch import apply_patch


@handle_exceptions(default_return_value=False, raise_on_error=False)
def apply_diff_to_file(
    diff: str,
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents"""
    skip_ci = base_args.get("skip_ci", False)
    message = f"Update {file_path} [skip ci]" if skip_ci else f"Update {file_path}"
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
            return f"file_path: '{file_path}' returned multiple files '{file_info}'. Please specify a single file path."

        # Return if the file_path is a directory. See Example2 at https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
        if file_info.get("type") == "dir":
            return f"file_path: '{file_path}' is a directory. It should be a file path."

        # Get the original text and SHA of the file
        s1: str = file_info.get("content", "")
        # content is base64 encoded by default in GitHub API
        original_text = base64.b64decode(s=s1).decode(encoding=UTF8, errors="replace")
        sha: str = file_info.get("sha", "")

    # Check for deletion diff (safety check)
    if "+++ /dev/null" in diff:
        return f"Cannot delete files using apply_diff_to_file. Use the delete_file tool instead for file path: {file_path}"

    # Create a new commit
    modified_text, rej_text = apply_patch(original_text=original_text, diff_text=diff)

    if modified_text == "":
        return f"diff format is incorrect. No changes were made to the file: {file_path}. Review the diff, correct it, and try again.\n\n{diff=}"

    if modified_text != "" and rej_text != "":
        return f"diff partially applied to the file: {file_path}. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\n{diff=}\n\n{rej_text=}"

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
                file_content=modified_text,
                eslint_config_content=eslint_config["content"],
                package_json_content=package_json_content,
            )
            if eslint_result and eslint_result["fixed_content"]:
                modified_text = eslint_result["fixed_content"]
        else:
            print(
                f"No ESLint config found for {owner}/{repo}, skipping ESLint validation"
            )

    # Normal file update
    s2 = modified_text.encode(encoding=UTF8)
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
    return f"diff applied to the file: {file_path} successfully by {apply_diff_to_file.__name__}()."
