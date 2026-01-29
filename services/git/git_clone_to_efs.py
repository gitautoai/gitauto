import asyncio
import os

from utils.command.run_subprocess_async import run_subprocess_async
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# clone_tasks example:
# {
#   "/mnt/efs/owner1/repo1": Task[str | None],
#   "/mnt/efs/owner2/repo2": Task[str | None]
# }
clone_tasks: dict[str, asyncio.Task[str | None]] = {}


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def git_clone_to_efs(efs_dir: str, clone_url: str, branch: str):
    logger.info("Cloning base to EFS: branch=%s dir=%s", branch, efs_dir)
    os.makedirs(efs_dir, exist_ok=True)

    # Lambda /var/task is read-only; redirect git config to /tmp
    # GIT_CONFIG_GLOBAL only affects git, unlike HOME which affects all tools
    os.environ["GIT_CONFIG_GLOBAL"] = "/tmp/.gitconfig"

    # EFS directories may be owned by different Lambda instances; mark as safe
    await run_subprocess_async(
        ["git", "config", "--global", "--add", "safe.directory", efs_dir], efs_dir
    )

    efs_git_dir = os.path.join(efs_dir, ".git")
    if os.path.exists(efs_git_dir):
        logger.info("EFS already has .git at %s, ensuring latest", efs_dir)

        # EFS persists across Lambda invocations; origin URL may contain expired token
        # Check if origin remote exists (may be missing if previous clone was interrupted)
        returncode, _ = await run_subprocess_async(
            ["git", "remote", "get-url", "origin"], efs_dir
        )
        if returncode == 0:
            # Origin exists, update URL with fresh token
            await run_subprocess_async(
                ["git", "remote", "set-url", "origin", clone_url], efs_dir
            )
        else:
            # Origin missing (incomplete previous clone), add it
            await run_subprocess_async(
                ["git", "remote", "add", "origin", clone_url], efs_dir
            )

        returncode, _ = await run_subprocess_async(
            ["git", "fetch", "--depth", "1", "origin", branch], efs_dir
        )
        if returncode == 0:
            fetch_head = os.path.join(efs_git_dir, "FETCH_HEAD")
            if os.path.exists(fetch_head):
                with open(fetch_head, encoding="utf-8") as f:
                    logger.info("FETCH_HEAD: %s", f.read().strip())
            else:
                logger.warning("FETCH_HEAD missing despite fetch success")
            await run_subprocess_async(
                ["git", "reset", "--hard", "FETCH_HEAD"], efs_dir
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
