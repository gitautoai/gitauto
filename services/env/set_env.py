# pylint: disable=unused-argument
import os

from anthropic.types import ToolUnionParam

from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

SET_ENV: ToolUnionParam = {
    "name": "set_env",
    "description": "Sets an environment variable that all subsequent subprocess calls (jest, eslint, prettier, tsc, etc.) inherit. Use this to fix environment issues like overriding distro detection, setting tool paths, or configuring runtime behavior. Example: set MONGOMS_DISTRO=ubuntu-22.04 when MongoMemoryServer can't find a binary for the current OS.",
    "input_schema": {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "The environment variable name. For example, 'MONGOMS_DISTRO'.",
            },
            "value": {
                "type": "string",
                "description": "The value to set. For example, 'ubuntu-22.04'.",
            },
        },
        "required": ["key", "value"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value="Failed to set environment variable.", raise_on_error=False
)
def set_env(*, key: str, value: str, base_args: BaseArgs, **_kwargs):
    """Set an environment variable that all subsequent subprocess calls inherit."""
    previous = os.environ.get(key)
    os.environ[key] = value
    logger.info("set_env: %s: %s -> %s", key, previous, value)
    return f"Environment variable {key} has been set."
