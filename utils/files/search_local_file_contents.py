from anthropic.types import ToolUnionParam

from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.grep_files import grep_files
from utils.logging.logging_config import logger

SEARCH_LOCAL_FILE_CONTENT: ToolUnionParam = {
    "name": "search_local_file_contents",
    "description": "Search for keywords in the local clone of the repository (PR branch). Returns matching file paths AND the matching lines with line numbers. Use this to find files containing specific variable names, function names, class names, or other identifiers. Especially if you change variable definitions, as they are likely used elsewhere. To reduce bugs, search multiple times from as many angles as possible.",
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

# Cap matching lines per file to avoid huge outputs from lockfiles etc.
MAX_LINES_PER_FILE = 10


@handle_exceptions(default_return_value="", raise_on_error=False)
def search_local_file_contents(query: str, base_args: BaseArgs, **_kwargs):
    """Search for a keyword in the local clone directory using grep."""
    clone_dir = base_args["clone_dir"]
    matches = grep_files(query=query, search_dir=clone_dir)

    if not matches:
        msg = f"0 files found for the search query '{query}'.\n"
        logger.info(msg)
        return msg

    total_files = len(matches)
    items = list(matches.items())[:20]
    result_lines: list[str] = []
    for fp, lines in items:
        for line in lines[:MAX_LINES_PER_FILE]:
            result_lines.append(f"{fp}:{line}")
        if len(lines) > MAX_LINES_PER_FILE:
            result_lines.append(f"{fp}: ... and {len(lines) - MAX_LINES_PER_FILE} more")
    msg = f"{total_files} files found for the search query '{query}':\n" + "\n".join(
        result_lines
    )
    if total_files > 20:
        msg += f"\n... and {total_files - 20} more files"
    msg += "\n"
    logger.info(msg)
    return msg
