# Third party imports
from anthropic.types import ToolUnionParam

# Local imports
from constants.claude import ClaudeModelId
from services.claude.chat_with_claude_simple import chat_with_claude_simple
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.logging.logging_config import logger

QUERY_FILE: ToolUnionParam = {
    "name": "query_file",
    "description": (
        "Ask a question about a file without loading its full content into context. "
        "The file is read by a faster model that returns only the answer. "
        "Use when you need to know something ABOUT a file (patterns, conventions, "
        "framework, structure) but don't need the exact code for editing. "
        "Use get_local_file_content instead when you need exact code to edit."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "File path relative to the repository root.",
            },
            "prompt": {
                "type": "string",
                "description": "What to find out about the file. Be specific.",
            },
        },
        "required": ["file_path", "prompt"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value="Failed to query file.", raise_on_error=False)
def query_file(file_path: str, prompt: str, base_args: dict, **_kwargs):
    usage_id = base_args.get("usage_id", 0)
    clone_dir = base_args.get("clone_dir", "")

    content = read_local_file(file_path=file_path, base_dir=clone_dir)
    if content is None:
        return f"File not found: '{file_path}'. Check the file path and try again."

    formatted = format_content_with_line_numbers(file_path=file_path, content=content)
    file_chars = len(formatted)

    logger.info("query_file: sending %d chars of '%s' to Haiku", file_chars, file_path)
    answer = chat_with_claude_simple(
        system_input=f"You are analyzing the file '{file_path}'. Answer the question based only on the file content.",
        user_input=f"{formatted}\n\n---\n\n{prompt}",
        usage_id=usage_id,
        model_id=ClaudeModelId.HAIKU_4_5,
    )

    answer_chars = len(answer) if answer else 0
    logger.info(
        "query_file: got %d char answer for %d char file '%s'",
        answer_chars,
        file_chars,
        file_path,
    )
    return answer
