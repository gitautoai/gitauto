import os

from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def git_clone_to_tmp(clone_dir: str, clone_url: str, branch: str):
    clone_git_dir = os.path.join(clone_dir, ".git")
    if os.path.exists(clone_git_dir):
        # Already cloned (e.g. Lambda reuse or retry) — update in place
        logger.info("Existing clone at %s, fetching branch %s", clone_dir, branch)

        # Update origin URL (token may have expired between Lambda invocations)
        try:
            run_subprocess(["git", "remote", "get-url", "origin"], clone_dir)
            run_subprocess(["git", "remote", "set-url", "origin", clone_url], clone_dir)
        except ValueError:
            logger.warning("Origin remote missing at %s, adding it", clone_dir)
            run_subprocess(["git", "remote", "add", "origin", clone_url], clone_dir)

        # --depth 1: only fetch the latest commit (saves time and disk)
        run_subprocess(["git", "fetch", "--depth", "1", "origin", branch], clone_dir)

        # -f: discard local changes, -B: create or reset branch to FETCH_HEAD
        # FETCH_HEAD: ref written by git fetch pointing to the fetched commit (more reliable than origin/branch in shallow clones)
        run_subprocess(["git", "checkout", "-f", "-B", branch, "FETCH_HEAD"], clone_dir)
        logger.info("Updated clone: %s @ %s", clone_dir, branch)
        return clone_dir

    # Fresh clone — single git command, no intermediate steps
    logger.info("Shallow cloning: branch=%s dir=%s", branch, clone_dir)
    os.makedirs(clone_dir, exist_ok=True)
    # --depth 1: shallow clone (latest commit only), -b: checkout this branch
    run_subprocess(
        ["git", "clone", "--depth", "1", "-b", branch, clone_url, clone_dir],
        clone_dir,
    )
    logger.info("Clone completed: %s @ %s", clone_dir, branch)
    return clone_dir
