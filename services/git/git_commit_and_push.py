from services.git.format_commit_message import format_commit_message
from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
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
    run_subprocess(push_cmd, clone_dir)

    logger.info("Committed and pushed: %s", message.split("\n")[0])
    return True
