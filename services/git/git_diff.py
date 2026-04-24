from anthropic.types import ToolUnionParam

from services.claude.tools.properties import FILE_PATH
from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

GIT_DIFF: ToolUnionParam = {
    "name": "git_diff",
    "description": (
        "Get the git diff between the base branch and HEAD. "
        "If file_path is omitted, returns the diff for all changed files."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                **FILE_PATH,
                "description": "Path to a specific file. Omit to get diff for all changed files.",
            },
        },
        "required": [],
        "additionalProperties": False,
    },
}


@handle_exceptions(default_return_value="Failed to get git diff.", raise_on_error=False)
def git_diff(
    base_args: BaseArgs,
    file_path: str | None = None,
    **_kwargs,
):
    clone_dir = base_args["clone_dir"]
    base_branch = base_args["base_branch"]

    # origin/ = remote-tracking ref (local branch doesn't exist in Lambda clones)
    # ...     = three-dot: diff from merge-base to HEAD (only PR's own changes)
    # HEAD    = current commit on the PR branch
    cmd = ["git", "diff", f"origin/{base_branch}...HEAD"]
    if file_path:
        logger.info("git_diff: scoping to file_path=%s", file_path)
        cmd.extend(["--", file_path.strip("/")])

    result = run_subprocess(args=cmd, cwd=clone_dir)

    diff = result.stdout
    if not diff:
        logger.info("No diff found for %s", file_path or "all files")
        return f"No diff found for {file_path or 'any files'} between origin/{base_branch} and HEAD."

    # Cap output to avoid blowing up context
    max_chars = 50_000
    if len(diff) > max_chars:
        logger.info("Diff truncated from %d to %d chars", len(diff), max_chars)
        diff = diff[:max_chars] + f"\n... [truncated, {len(diff):,} chars total]"

    logger.info("Returning diff for %s (%d chars)", file_path or "all files", len(diff))
    return diff
