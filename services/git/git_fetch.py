from utils.command.run_subprocess_async import run_subprocess_async
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def git_fetch(target_dir: str, clone_url: str, branch: str):
    # --depth 1 for shallow fetch to save disk space and time
    # Syntax: git fetch [options] <repository> <refspec>
    returncode, _ = await run_subprocess_async(
        ["git", "fetch", "--depth", "1", clone_url, branch], target_dir
    )
    if returncode != 0:
        return False

    logger.info("git fetch completed: %s", target_dir)
    return True
