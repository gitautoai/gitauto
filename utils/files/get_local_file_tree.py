import os

from anthropic.types import ToolUnionParam

from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

GET_LOCAL_FILE_TREE: ToolUnionParam = {
    "name": "get_local_file_tree",
    "description": "Lists files and directories at a specific directory path in the local clone. Works like 'ls' command - shows contents of the specified directory, or root if no dir_path specified. Can see node_modules if dependencies have been installed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Directory path to list contents of. Use empty string or omit for root directory. Examples: 'src', 'node_modules/@aws-sdk', 'dist'.",
            }
        },
        "additionalProperties": False,
    },
}


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_local_file_tree(base_args: BaseArgs, dir_path: str = "", **_kwargs):
    clone_dir = base_args["clone_dir"]
    result: list[str] = []

    if not dir_path or dir_path == ".":
        target_dir = clone_dir
    else:
        target_dir = os.path.join(clone_dir, dir_path.strip("/"))

    if not os.path.isdir(target_dir):
        msg = f"Directory '{dir_path}' not found."
        logger.info(msg)
        return result

    entries = os.listdir(target_dir)
    dirs: list[str] = []
    files: list[str] = []

    for entry in entries:
        full_path = os.path.join(target_dir, entry)
        if os.path.isdir(full_path):
            dirs.append(f"{entry}/")
        else:
            files.append(entry)

    result = sorted(dirs) + sorted(files)
    return result
