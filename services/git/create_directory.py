import os

from anthropic.types import ToolUnionParam

from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

CREATE_DIRECTORY: ToolUnionParam = {
    "name": "create_directory",
    "description": "Creates a new directory in the repository. Use this BEFORE writing files to a new directory path that doesn't exist yet. This helps organize test files and source files in the correct location.",
    "input_schema": {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Directory path to create. For example, if 'src/components/auth' doesn't exist and you need to write a file there, pass 'src/components/auth'.",
            },
        },
        "required": ["dir_path"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value="Failed to create directory.", raise_on_error=False
)
def create_directory(dir_path: str, base_args: BaseArgs, **_kwargs):
    """Create a directory in the local clone for subsequent file writes."""
    clone_dir = base_args["clone_dir"]
    full_path = os.path.join(clone_dir, dir_path.strip("/"))

    os.makedirs(full_path, exist_ok=True)
    logger.info("Created directory: %s", full_path)

    return (
        f"Created directory '{dir_path}'. You can now write files into this directory."
    )
