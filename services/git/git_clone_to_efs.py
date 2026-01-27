import os

from utils.command.run_subprocess_async import run_subprocess_async
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def git_clone_to_efs(efs_dir: str, clone_url: str, branch: str):
    logger.info("Cloning base to EFS: branch=%s dir=%s", branch, efs_dir)
    os.makedirs(efs_dir, exist_ok=True)

    efs_git_dir = os.path.join(efs_dir, ".git")
    if os.path.exists(efs_git_dir):
        logger.info(
            "EFS already has .git at %s, skipping clone. Contents: %s",
            efs_dir,
            os.listdir(efs_dir),
        )
        return efs_dir

    # Always use init + fetch + checkout instead of clone
    # Avoids race condition where install_node_packages writes files before clone completes
    await run_subprocess_async(["git", "init"], efs_dir)
    await run_subprocess_async(["git", "remote", "add", "origin", clone_url], efs_dir)
    await run_subprocess_async(
        ["git", "fetch", "--depth", "1", "origin", branch], efs_dir
    )
    await run_subprocess_async(["git", "checkout", "-f", branch], efs_dir)

    logger.info("git clone completed: %s", efs_dir)
    return efs_dir
