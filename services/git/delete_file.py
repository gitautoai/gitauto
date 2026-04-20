# Standard imports
import os
import subprocess

# Third party imports
from anthropic.types import ToolUnionParam

# Local imports
from services.claude.tools.properties import FILE_PATH
from services.git.git_commit_and_push import git_commit_and_push
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
DELETE_FILE: ToolUnionParam = {
    "name": "delete_file",
    "description": "Deletes a file from the GitHub repository. Use this to remove unused or duplicate files that cause conflicts.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
        },
        "required": ["file_path"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_file(
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Delete a file from the local clone, then commit and push to the PR branch."""
    clone_dir = base_args["clone_dir"]
    local_path = os.path.join(clone_dir, file_path)

    if os.path.isdir(local_path):
        logger.info("delete_file: %s is a directory, returning error", file_path)
        return f"Error: '{file_path}' is a directory, not a file"

    if not os.path.exists(local_path):
        logger.info("delete_file: %s not found, returning error", file_path)
        return f"Error: File {file_path} not found"

    # Sentry AGENT-36X/36W/344 fired with: `git add mongodb-binaries/mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz.md5` → "pathspec did not match any files". The path is gitignored (mongodb-memory-server writes there) so it was never in git's index, and os.remove above cleared it from disk, leaving `git add` with nothing to match. Check tracking BEFORE os.remove so we can skip the commit when the path was never tracked.
    ls_files = subprocess.run(
        ["git", "ls-files", "--error-unmatch", file_path],
        cwd=clone_dir,
        capture_output=True,
        check=False,
    )
    is_tracked = ls_files.returncode == 0

    os.remove(local_path)
    logger.info("Deleted local: %s", local_path)

    if not is_tracked:
        logger.info(
            "delete_file: %s is not tracked by git (gitignored or never committed); skipping commit",
            file_path,
        )
        return f"File {file_path} successfully deleted"

    git_commit_and_push(
        base_args=base_args, message=f"Delete {file_path}", files=[file_path]
    )

    logger.info("delete_file: %s deleted and commit pushed", file_path)
    return f"File {file_path} successfully deleted"
