import asyncio
import os

from services.efs.get_efs_dir import get_efs_dir
from services.git.get_clone_dir import get_clone_dir
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
async def clone_repo(
    owner: str, repo: str, pr_number: int | None, branch: str, token: str
):
    """Clone to /tmp, not EFS, because EFS is shared across Lambda invocations and concurrent PRs would conflict. /tmp works for both Lambda and Mac local (/private/tmp on Mac)."""
    clone_dir = get_clone_dir(owner, repo, pr_number)

    if os.path.exists(clone_dir):
        logger.info("Reusing existing clone: %s", clone_dir)
        return clone_dir

    repo_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    logger.info("Clone started: branch=%s dir=%s", branch, clone_dir)

    # --depth 1 (shallow clone): only need current files for code quality tools, not git history
    process = await asyncio.create_subprocess_exec(
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        branch,
        repo_url,
        clone_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(process.communicate(), timeout=180)

    if process.returncode != 0:
        logger.error("Clone failed: %s", stderr.decode())
        raise RuntimeError(f"git clone failed: {stderr.decode()}")

    logger.info("Clone completed: %s", clone_dir)

    efs_node_modules = os.path.join(get_efs_dir(owner, repo), "node_modules")
    clone_node_modules = os.path.join(clone_dir, "node_modules")
    if os.path.exists(efs_node_modules) and not os.path.exists(clone_node_modules):
        os.symlink(efs_node_modules, clone_node_modules)
        logger.info(
            "Symlinked node_modules: %s -> %s", clone_node_modules, efs_node_modules
        )

    return clone_dir
