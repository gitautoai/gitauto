from dataclasses import dataclass, field

from services.git.format_commit_message import format_commit_message
from services.git.get_branch_head_author import get_branch_head_author
from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.git.is_path_gitignored import is_path_gitignored
from utils.logging.logging_config import logger


@dataclass
class GitCommitResult:
    success: bool = False
    concurrent_push_detected: bool = False
    # Paths the caller asked us to commit that are gitignored and were dropped from the stage list.
    # Empty when nothing was dropped.
    gitignored_paths: list[str] = field(default_factory=list)


@handle_exceptions(raise_on_error=True)
def git_commit_and_push(
    base_args: BaseArgs,
    message: str,
    files: list[str],
    force: bool = False,
):
    clone_dir = base_args["clone_dir"]
    clone_url = base_args["clone_url"]
    new_branch = base_args["new_branch"]
    skip_ci = base_args.get("skip_ci", False)

    # Drop gitignored paths from the stage list.
    # Without this, `git add` fails with "paths are ignored by one of your .gitignore files" and the agent has wasted an edit turn on a path it shouldn't have touched (e.g. node_modules after a search_and_replace on an installed dependency, see AGENT-3J4).
    # Surface the first skipped path on the result so the caller can warn the agent; commit the rest.
    gitignored = [f for f in files if is_path_gitignored(clone_dir, f)]
    if gitignored:
        logger.warning(
            "git_commit_and_push: dropping %d gitignored path(s) from stage list: %s",
            len(gitignored),
            gitignored,
        )
        files = [f for f in files if f not in gitignored]
    if not files:
        logger.warning(
            "git_commit_and_push: every requested file is gitignored, nothing to commit"
        )
        return GitCommitResult(success=False, gitignored_paths=gitignored)

    # Stage specified files (handles new, modified, and deleted files)
    run_subprocess(["git", "add"] + files, clone_dir)

    if skip_ci:
        logger.info("git_commit_and_push: appending [skip ci] to message")
        message = f"{message} [skip ci]"
    message = format_commit_message(message=message, base_args=base_args)

    # -m: commit message inline (not opening an editor)
    run_subprocess(["git", "commit", "-m", message], clone_dir)

    # Update remote URL with fresh token and push
    run_subprocess(["git", "remote", "set-url", "origin", clone_url], clone_dir)
    push_cmd = ["git", "push"]
    if force:
        logger.info("git_commit_and_push: force push via --force-with-lease")
        push_cmd.append("--force-with-lease")
    push_cmd.extend(["origin", f"HEAD:refs/heads/{new_branch}"])

    try:
        run_subprocess(push_cmd, clone_dir)
    except ValueError as err:
        err_text = str(err)
        if "fetch first" not in err_text and "non-fast-forward" not in err_text:
            logger.error("git push failed with unhandled error: %s", err_text)
            raise

        # Sentry AGENT-36T had this issue
        author = get_branch_head_author(clone_dir, clone_url, new_branch)
        logger.warning(
            "git_commit_and_push bailing on %s: racer=%s advanced the branch (human or other GitAuto invocation). Not rebasing — would clobber their intent. Signaling concurrent_push_detected so the caller chain can break the agent loop cleanly and still run its cleanup.",
            new_branch,
            author,
        )
        return GitCommitResult(success=False, concurrent_push_detected=True)

    logger.info("Committed and pushed: %s", message.split("\n")[0])
    return GitCommitResult(success=True, gitignored_paths=gitignored)
