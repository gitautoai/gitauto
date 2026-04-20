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

OLD_STRING: dict[str, str] = {
    "type": "string",
    "description": "The exact string to find in the file. Must match exactly ONE location. If it matches multiple locations, add more surrounding context lines to make it unique.",
}
NEW_STRING: dict[str, str] = {
    "type": "string",
    "description": "The replacement string. Can be empty to delete the matched text.",
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
SEARCH_AND_REPLACE: ToolUnionParam = {
    "name": "search_and_replace",
    "description": "Edits an EXISTING file by finding an exact string match and replacing it. More reliable than apply_diff_to_file because it uses content matching instead of line numbers. Use this for targeted edits to existing files.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
            "old_string": OLD_STRING,
            "new_string": NEW_STRING,
        },
        "required": ["file_path", "old_string", "new_string"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value=lambda old_string, new_string, file_path, base_args, **kwargs: FileWriteResult(
        success=False,
        message="Unexpected error occurred.",
        file_path=file_path,
        content="",
    ),
    raise_on_error=False,
)
def search_and_replace(
    old_string: str,
    new_string: str,
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    clone_dir = base_args["clone_dir"]
    local_path = os.path.join(clone_dir, file_path)

    # Check if path is a directory
    if os.path.isdir(local_path):
        logger.warning(
            "search_and_replace: %s is a directory, not a file; aborting", file_path
        )
        return FileWriteResult(
            success=False,
            message=f"'{file_path}' is a directory, not a file.",
            file_path=file_path,
            content="",
        )

    # Read the existing file
    original_text = read_local_file(file_path, clone_dir)
    if original_text is None:
        logger.warning(
            "search_and_replace: %s not found in clone_dir; aborting", file_path
        )
        return FileWriteResult(
            success=False,
            message=f"File '{file_path}' not found.",
            file_path=file_path,
            content="",
        )

    # Reject empty old_string
    if not old_string:
        logger.warning(
            "search_and_replace: empty old_string for %s; aborting", file_path
        )
        return FileWriteResult(
            success=False,
            message="old_string must not be empty. Provide the exact text to find.",
            file_path=file_path,
            content=original_text,
        )

    # Normalize line endings in old_string/new_string to match the file
    original_line_break = detect_line_break(text=original_text)
    if original_line_break != "\n":
        logger.info(
            "search_and_replace: normalizing old_string/new_string line endings to %r to match %s",
            original_line_break,
            file_path,
        )
        old_string = old_string.replace("\n", original_line_break)
        new_string = new_string.replace("\n", original_line_break)

    # Count occurrences
    count = original_text.count(old_string)
    if count == 0:
        logger.warning(
            "search_and_replace: old_string not found in %s; agent must adjust",
            file_path,
        )
        return FileWriteResult(
            success=False,
            message=f"old_string not found in '{file_path}'. Verify the exact text including whitespace and indentation.",
            file_path=file_path,
            content=original_text,
        )
    if count > 1:
        logger.warning(
            "search_and_replace: old_string matches %d times in %s; agent must add context for uniqueness",
            count,
            file_path,
        )
        return FileWriteResult(
            success=False,
            message=f"old_string found {count} times in '{file_path}'. Add more surrounding context to make it unique.",
            file_path=file_path,
            content=original_text,
        )

    # Replace exactly once
    new_content = original_text.replace(old_string, new_string, 1)

    # Post-process
    new_content = sort_imports(new_content, file_path)
    new_content = strip_trailing_spaces(new_content)
    new_content = ensure_final_newline(new_content)

    # Skip if content is identical after processing
    if new_content == original_text:
        logger.info("No changes to %s, skipping", file_path)
        return FileWriteResult(
            success=True,
            message=f"No changes to {file_path}.",
            file_path=file_path,
            content=new_content,
        )

    # Compute unified diff for agent feedback
    diff_text = compute_unified_diff(original_text, new_content, file_path)

    # Write file to local clone (newline="" preserves CRLF if present)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding=UTF8, newline="") as f:
        f.write(new_content)
    logger.info("Updated: %s", local_path)

    commit_result = git_commit_and_push(
        base_args=base_args, message=f"Update {file_path}", files=[file_path]
    )
    if not commit_result.success:
        logger.warning(
            "search_and_replace: push for %s failed (concurrent_push_detected=%s on %s)",
            file_path,
            commit_result.concurrent_push_detected,
            base_args["new_branch"],
        )
        return FileWriteResult(
            success=False,
            message=(
                f"Concurrent push detected on `{base_args['new_branch']}` while committing {file_path}. Another commit landed; aborting this edit."
                if commit_result.concurrent_push_detected
                else f"Failed to commit/push {file_path}."
            ),
            file_path=file_path,
            content="",
            concurrent_push_detected=commit_result.concurrent_push_detected,
        )

    logger.info("search_and_replace: %s committed and pushed", file_path)
    return FileWriteResult(
        success=True,
        message=f"Updated {file_path}.",
        file_path=file_path,
        content=new_content,
        diff=diff_text,
    )
