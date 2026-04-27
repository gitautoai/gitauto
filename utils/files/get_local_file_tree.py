import os

from anthropic.types import ToolUnionParam

from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.list_local_directory import list_local_directory
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
    if not dir_path or dir_path == ".":
        logger.info("get_local_file_tree: empty/dot dir_path, using clone_dir")
        target_dir = clone_dir
    else:
        logger.info("get_local_file_tree: joining %s under clone_dir", dir_path)
        target_dir = os.path.join(clone_dir, dir_path.strip("/"))

    return list_local_directory(target_dir)
