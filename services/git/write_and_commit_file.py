# Standard imports
import os

# Third party imports
from anthropic.types import ToolUnionParam

# Local imports
from config import UTF8
from services.claude.tools.file_modify_result import FileWriteResult
from services.claude.tools.properties import FILE_PATH
from services.git.git_commit_and_push import git_commit_and_push
from services.types.base_args import BaseArgs
from utils.diff.compute_unified_diff import compute_unified_diff
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger
from utils.new_lines.detect_new_line import detect_line_break
from utils.text.ensure_final_newline import ensure_final_newline
from utils.text.sort_imports import sort_imports
from utils.text.strip_trailing_spaces import strip_trailing_spaces

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
WRITE_AND_COMMIT_FILE: ToolUnionParam = {
    "name": "write_and_commit_file",
    "description": "Replaces the entire content of a file and commits the change to the PR branch. Use this to create NEW files or when the entire file needs to be rewritten. For targeted edits to existing files, prefer search_and_replace instead.",
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
        logger.warning(
            "write_and_commit_file: %s is a directory, not a file; aborting", file_path
        )
        return FileWriteResult(
            success=False,
            message=f"'{file_path}' is a directory, not a file.",
            file_path=file_path,
            content="",
        )

    # Determine commit message before writing (os.path.exists changes after write)
    file_exists = os.path.exists(local_path)
    default_message = f"Update {file_path}" if file_exists else f"Create {file_path}"

    existing_content = read_local_file(file_path, clone_dir)
    if existing_content is not None:
        logger.info(
            "write_and_commit_file: %s exists; normalizing line endings before compare",
            file_path,
        )

        # Claude's JSON output always uses LF. Convert to match the original line endings.
        original_line_break = detect_line_break(text=existing_content)
        if original_line_break != "\n":
            logger.info(
                "write_and_commit_file: converting new content from LF to %r to match existing file %s",
                original_line_break,
                file_path,
            )
            file_content = file_content.replace("\n", original_line_break)

        if existing_content == file_content:
            logger.info("No changes to %s, skipping", file_path)
            return FileWriteResult(
                success=True,
                message=f"No changes to {file_path}.",
                file_path=file_path,
                content=file_content,
            )

    # Compute unified diff to include in the tool result so the agent sees its changes
    diff_text = ""
    if existing_content is not None:
        logger.info(
            "write_and_commit_file: computing unified diff for %s to return with tool result",
            file_path,
        )
        diff_text = compute_unified_diff(existing_content, file_content, file_path)

    # Write file to local clone (newline="" preserves CRLF if present)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding=UTF8, newline="") as f:
        f.write(file_content)
    logger.info("%s: %s", "Updated" if file_exists else "Created", local_path)

    # Commit and push (mirrors original GitHub Contents API behavior: 1 commit per file edit)
    message = commit_message if commit_message else default_message
    commit_result = git_commit_and_push(
        base_args=base_args, message=message, files=[file_path]
    )
    if not commit_result.success:
        logger.warning(
            "write_and_commit_file: push on %s failed (concurrent_push_detected=%s on branch %s). Returning success=False so chat_with_agent can break the loop.",
            file_path,
            commit_result.concurrent_push_detected,
            base_args["new_branch"],
        )
        return FileWriteResult(
            success=False,
            message=(
                f"Concurrent push detected on `{base_args['new_branch']}` while committing {file_path}. Another commit landed on the branch; aborting this edit."
                if commit_result.concurrent_push_detected
                else f"Failed to commit/push {file_path}."
            ),
            file_path=file_path,
            content="",
            concurrent_push_detected=commit_result.concurrent_push_detected,
        )

    logger.info(
        "write_and_commit_file succeeded on %s; returning FileWriteResult(success=True)",
        file_path,
    )
    return FileWriteResult(
        success=True,
        message=f"{'Updated' if file_exists else 'Created'} {file_path}.",
        file_path=file_path,
        content=file_content,
        diff=diff_text,
    )
