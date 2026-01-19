import asyncio

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def git_checkout(target_dir: str, branch: str):
    logger.info("Checking out branch %s in %s", branch, target_dir)

    # Syntax: git checkout [options] <branch> [<start-point>]
    # -f discards local changes, -B creates/resets branch to FETCH_HEAD (set by prior git fetch)
    cmd = ["git", "-C", target_dir, "checkout", "-f", "-B", branch, "FETCH_HEAD"]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error("git checkout in %s failed: %s", target_dir, stderr.decode())
        return False

    logger.info("git checkout completed: %s", target_dir)
    return True
