import asyncio
import os

from services.git.remove_stale_git_locks import remove_stale_git_locks
from utils.command.run_subprocess_async import run_subprocess_async
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

LOCK_POLL_SECONDS = 5


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def git_reset(target_dir: str):
    git_dir = os.path.join(target_dir, ".git")

    # Remove any stale locks left by killed Lambda invocations
    remove_stale_git_locks(git_dir)

    # Wait for fresh index.lock — another process is actively writing
    lock_file = os.path.join(git_dir, "index.lock")
    waited = False

    while os.path.exists(lock_file):
        waited = True
        logger.info("Waiting for index.lock: %s", lock_file)
        await asyncio.sleep(LOCK_POLL_SECONDS)

    # If we waited for another process, it already fetched+reset the same branch
    if waited:
        logger.info("index.lock released, repo already updated: %s", target_dir)
        return True

    # Reset to FETCH_HEAD after git_fetch has been called
    returncode, _ = await run_subprocess_async(
        ["git", "reset", "--hard", "FETCH_HEAD"], target_dir
    )
    if returncode != 0:
        return False

    logger.info("git reset --hard FETCH_HEAD completed: %s", target_dir)
    return True
