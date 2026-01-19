import asyncio

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def git_fetch(target_dir: str, clone_url: str, branch: str):
    # --depth 1 for shallow fetch to save disk space and time
    # Syntax: git fetch [options] <repository> <refspec>
    cmd = ["git", "-C", target_dir, "fetch", "--depth", "1", clone_url, branch]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error("git fetch to %s failed: %s", target_dir, stderr.decode())
        return False

    logger.info("git fetch completed: %s", target_dir)
    return True
