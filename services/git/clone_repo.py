import asyncio
import os

from services.efs.get_efs_dir import get_efs_dir
from services.git.get_clone_dir import get_clone_dir
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
async def clone_repo(
    owner: str, repo: str, pr_number: int | None, branch: str, token: str
):
    """Clone to /tmp, not EFS, because EFS is shared across Lambda invocations and concurrent PRs would conflict. /tmp works for both Lambda and Mac local (/private/tmp on Mac)."""
    clone_dir = get_clone_dir(owner, repo, pr_number)

    if os.path.exists(clone_dir):
        print(f"Reusing existing clone: {clone_dir}")
        return clone_dir

    repo_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

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
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)

    if process.returncode != 0:
        raise RuntimeError(f"git clone failed: {stderr.decode()}")

    efs_node_modules = os.path.join(get_efs_dir(owner, repo), "node_modules")
    clone_node_modules = os.path.join(clone_dir, "node_modules")
    if os.path.exists(efs_node_modules) and not os.path.exists(clone_node_modules):
        os.symlink(efs_node_modules, clone_node_modules)

    return clone_dir
