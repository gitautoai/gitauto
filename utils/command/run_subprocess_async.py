import asyncio

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
async def run_subprocess_async(cmd: list[str], cwd: str | None = None):
    if cwd:
        logger.info("Running %s in %s", cmd[0], cwd)
    else:
        logger.info("Running %s", cmd[0])
    process = await asyncio.create_subprocess_exec(
        *cmd, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        logger.error("%s in %s failed: %s", cmd[0], cwd, stderr.decode())
        raise RuntimeError(f"Command {cmd[0]} failed: {stderr.decode()}")
