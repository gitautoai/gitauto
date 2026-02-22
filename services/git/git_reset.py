import os

from services.git.resolve_git_locks import resolve_git_locks
from utils.command.run_subprocess_async import run_subprocess_async
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def git_reset(target_dir: str):
    git_dir = os.path.join(target_dir, ".git")

    # Remove stale locks (>10min, crashed Lambda) and wait for fresh ones (concurrent Lambda)
    await resolve_git_locks(git_dir)

    # Reset to FETCH_HEAD after git_fetch has been called
    returncode, _ = await run_subprocess_async(
        ["git", "reset", "--hard", "FETCH_HEAD"], target_dir
    )
    if returncode != 0:
        return False

    logger.info("git reset --hard FETCH_HEAD completed: %s", target_dir)
    return True
