# Standard imports
import os

# Third party imports
from anthropic.types import ToolUnionParam

# Local imports
from config import UTF8
from services.claude.tools.file_modify_result import FileWriteResult
from services.claude.tools.properties import FILE_PATH
from services.git.git_commit_and_push import git_commit_and_push
from services.git.git_show_head_file import git_show_head_file
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.new_lines.detect_new_line import detect_line_break
from utils.text.ensure_final_newline import ensure_final_newline
from utils.text.sort_imports import sort_imports
from utils.text.strip_trailing_spaces import strip_trailing_spaces

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
WRITE_AND_COMMIT_FILE: ToolUnionParam = {
    "name": "write_and_commit_file",
    "description": "Replaces the entire content of a file and commits the change to the PR branch. Use this to create NEW files or when the entire file needs to be rewritten. For minor modifications to existing files, use apply_diff_to_file instead.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
            "file_content": {
                "type": "string",
                "description": "The new content to replace the existing file content with.",
            },
        },
        "required": ["file_path", "file_content"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value=lambda file_content, file_path, base_args, **kwargs: FileWriteResult(
        success=False,
        message="Unexpected error occurred.",
        file_path=file_path,
        content="",
    ),
    raise_on_error=False,
)
def write_and_commit_file(
    file_content: str,
    file_path: str,
    base_args: BaseArgs,
    commit_message: str | None = None,
    **_kwargs,
):
    """Replace a file's content in the local clone, then commit and push to the PR branch."""
    clone_dir = base_args["clone_dir"]
    local_path = os.path.join(clone_dir, file_path)

    # Sort imports, strip trailing spaces, and ensure final newline
    file_content = sort_imports(file_content, file_path)
    file_content = strip_trailing_spaces(file_content)
    file_content = ensure_final_newline(file_content)

    # Check if path is a directory
    if os.path.isdir(local_path):
        return FileWriteResult(
            success=False,
            message=f"'{file_path}' is a directory, not a file.",
            file_path=file_path,
            content="",
        )

    # Determine commit message before writing (os.path.exists changes after write)
    file_exists = os.path.exists(local_path)
    default_message = f"Update {file_path}" if file_exists else f"Create {file_path}"

    # Compare against last committed version (not disk, which formatters may have modified)
    existing_content = git_show_head_file(file_path=file_path, clone_dir=clone_dir)
    if existing_content is not None:

        # Claude's JSON output always uses LF. Convert to match the original line endings.
        original_line_break = detect_line_break(text=existing_content)
        if original_line_break != "\n":
            file_content = file_content.replace("\n", original_line_break)

        if existing_content == file_content:
            logger.info("No changes to %s, skipping", file_path)
            return FileWriteResult(
                success=True,
                message=f"No changes to {file_path}.",
                file_path=file_path,
                content=file_content,
            )

    # Write file to local clone (newline="" preserves CRLF if present)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding=UTF8, newline="") as f:
        f.write(file_content)
    logger.info("%s: %s", "Updated" if file_exists else "Created", local_path)

    # Commit and push (mirrors original GitHub Contents API behavior: 1 commit per file edit)
    message = commit_message if commit_message else default_message
    git_commit_and_push(base_args=base_args, message=message, files=[file_path])

    return FileWriteResult(
        success=True,
        message=f"{'Updated' if file_exists else 'Created'} {file_path}.",
        file_path=file_path,
        content=file_content,
    )
