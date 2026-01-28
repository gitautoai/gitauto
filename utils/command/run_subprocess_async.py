import asyncio

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(
    default_return_value=(1, "Exception in run_subprocess_async"), raise_on_error=False
)
async def run_subprocess_async(cmd: list[str], cwd: str | None = None):
    cmd_str = " ".join(cmd)
    if cwd:
        logger.info("Running `%s` in %s", cmd_str, cwd)
    else:
        logger.info("Running `%s`", cmd_str)

    process = await asyncio.create_subprocess_exec(
        *cmd, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        stderr_str = stderr.decode()
        logger.error("`%s` in %s failed: %s", cmd_str, cwd, stderr_str)
        return process.returncode, stderr_str

    return 0, stdout.decode()
