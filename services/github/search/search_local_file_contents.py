from anthropic.types import ToolUnionParam

from services.github.search.grep_files import grep_files
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

SEARCH_LOCAL_FILE_CONTENT: ToolUnionParam = {
    "name": "search_local_file_contents",
    "description": "Search for keywords in the local clone of the repository (PR branch). PREFERRED over search_remote_file_contents because this searches the actual PR branch, not just the default branch, and has no rate limiting. Use this to find files containing specific variable names, function names, class names, or other identifiers. Especially if you change variable definitions, as they are likely used elsewhere. To reduce bugs, search multiple times from as many angles as possible.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The keyword to search for. Use a single specific identifier (variable name, function name, class name). Regex is not supported.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value="", raise_on_error=False)
def search_local_file_contents(query: str, base_args: BaseArgs, **_kwargs):
    """Search for a keyword in the local clone directory using grep."""
    clone_dir = base_args["clone_dir"]
    file_paths = grep_files(query=query, search_dir=clone_dir)

    if not file_paths:
        msg = f"0 files found for the search query '{query}'.\n"
        logger.info(msg)
        return msg

    # Limit to 20 files to avoid overwhelming the agent
    total = len(file_paths)
    file_paths = file_paths[:20]

    msg = f"{total} files found for the search query '{query}':\n- " + "\n- ".join(
        file_paths
    )
    if total > 20:
        msg += f"\n... and {total - 20} more files"
    msg += "\n"
    logger.info(msg)
    return msg
