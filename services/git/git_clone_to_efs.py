import asyncio
import os

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def git_clone_to_efs(efs_dir: str, clone_url: str, branch: str):
    logger.info("Cloning base to EFS: branch=%s dir=%s", branch, efs_dir)
    os.makedirs(os.path.dirname(efs_dir), exist_ok=True)

    # --depth 1 for shallow clone to save disk space and clone time
    # Syntax: git clone [options] <repository> <directory>
    cmd = ["git", "clone", "--depth", "1", "--branch", branch, clone_url, efs_dir]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error("git clone to %s failed: %s", efs_dir, stderr.decode())
        raise RuntimeError(f"git clone failed: {stderr.decode()}")

    logger.info("git clone completed: %s", efs_dir)
    return efs_dir
