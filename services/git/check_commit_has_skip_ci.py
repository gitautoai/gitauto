from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_commit_has_skip_ci(commit_sha: str, clone_dir: str):
    """Checks if a commit message contains [skip ci] using git log.

    Requires clone_dir to be a valid git repo (EFS clone or local clone).
    """
    # Fetch to ensure we have the commit
    try:
        run_subprocess(args=["git", "fetch", "origin", commit_sha], cwd=clone_dir)
    except ValueError:
        logger.warning("Failed to fetch %s, trying with local data", commit_sha)

    # --format=%B: print only the commit message body (no hash, no author)
    # -1: show only one commit
    result = run_subprocess(
        args=["git", "log", "--format=%B", "-1", commit_sha],
        cwd=clone_dir,
    )
    message = result.stdout.strip() if result and result.stdout else ""
    return "[skip ci]" in message
