from anthropic.types import ToolUnionParam

from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

SWITCH_NODE_VERSION: ToolUnionParam = {
    "name": "switch_node_version",
    "description": "Switches the active Node.js version using `n`. Use this when you see NODE_MODULE_VERSION mismatch errors or need a specific Node version for the repo. The version is a major number like '20' or '18'.",
    "input_schema": {
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The Node.js major version to switch to. For example, '20', '18', '22'.",
            },
        },
        "required": ["version"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value="Failed to switch Node.js version.", raise_on_error=False
)
def switch_node_version(*, version: str, **_kwargs):
    """Switch Node.js to the specified major version using n."""
    logger.info("switch_node_version: Switching to Node %s", version)
    run_subprocess(["n", version], cwd="/tmp")
    logger.info("switch_node_version: Switched to Node %s", version)
    return f"Switched to Node.js {version}."
