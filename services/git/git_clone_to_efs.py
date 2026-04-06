import os

from services.git.resolve_git_locks import resolve_git_locks
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def git_clone_to_efs(efs_dir: str, clone_url: str, branch: str):
    logger.info("Cloning base to EFS: branch=%s dir=%s", branch, efs_dir)
    os.makedirs(efs_dir, exist_ok=True)

    # EFS directories may be owned by different Lambda instances; mark as safe
    run_subprocess(
        ["git", "config", "--global", "--add", "safe.directory", efs_dir], efs_dir
    )

    efs_git_dir = os.path.join(efs_dir, ".git")
    if os.path.exists(efs_git_dir):
        logger.info("EFS already has .git at %s, ensuring latest", efs_dir)

        # Remove stale locks (>10min, crashed Lambda) and wait for fresh ones (concurrent Lambda)
        resolve_git_locks(efs_git_dir)

        # EFS persists across Lambda invocations; origin URL may contain expired token
        # Check if origin remote exists (may be missing if previous clone was interrupted)
        try:
            run_subprocess(["git", "remote", "get-url", "origin"], efs_dir)
            # Origin exists, update URL with fresh token
            run_subprocess(["git", "remote", "set-url", "origin", clone_url], efs_dir)
        except ValueError:
            # Origin missing (incomplete previous clone), add it
            run_subprocess(["git", "remote", "add", "origin", clone_url], efs_dir)

        # Resolve locks again right before fetch to close the race window
        # (another Lambda may have created locks between the first resolve and now)
        resolve_git_locks(efs_git_dir)

        try:
            run_subprocess(["git", "fetch", "--depth", "1", "origin", branch], efs_dir)
        except ValueError:
            return efs_dir  # fetch failed, skip reset/checkout

        fetch_head_content = read_local_file("FETCH_HEAD", efs_git_dir)
        if fetch_head_content:
            logger.info("FETCH_HEAD: %s", fetch_head_content.strip())
        else:
            logger.warning("FETCH_HEAD missing despite fetch success")
        run_subprocess(["git", "reset", "--hard", "FETCH_HEAD"], efs_dir)
        # Switch HEAD to the correct branch if it changed (e.g. master → release/20260408)
        head_content = read_local_file("HEAD", efs_git_dir)
        current_ref = head_content.strip() if head_content else ""
        if current_ref != f"ref: refs/heads/{branch}":
            run_subprocess(["git", "checkout", "-B", branch, "FETCH_HEAD"], efs_dir)
        return efs_dir

    # Always use init + fetch + checkout instead of clone
    # Avoids race condition where install_node_packages writes files before clone completes
    run_subprocess(["git", "init"], efs_dir)
    run_subprocess(["git", "remote", "add", "origin", clone_url], efs_dir)
    run_subprocess(["git", "fetch", "--depth", "1", "origin", branch], efs_dir)
    run_subprocess(["git", "checkout", "-f", branch], efs_dir)
    logger.info("git clone completed: %s", efs_dir)
    return efs_dir
