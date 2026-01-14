import os
import subprocess

from services.efs.get_efs_dir import get_efs_dir
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def clone_repo(owner: str, repo: str, pr_number: int | None, branch: str, token: str):
    """Clone to /tmp, not EFS, because EFS is shared across Lambda invocations and concurrent PRs would conflict. /tmp works for both Lambda and Mac local (/private/tmp on Mac)."""
    if pr_number:
        clone_dir = f"/tmp/{owner}/{repo}/pr-{pr_number}"
    else:
        clone_dir = f"/tmp/{owner}/{repo}"

    if os.path.exists(clone_dir):
        print(f"Reusing existing clone: {clone_dir}")
        return clone_dir

    repo_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

    # --depth 1 (shallow clone): only need current files for code quality tools, not git history
    clone_cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        branch,
        repo_url,
        clone_dir,
    ]
    subprocess.run(clone_cmd, capture_output=True, text=True, check=True, timeout=180)

    # Symlink node_modules from EFS so eslint/prettier can find packages (skipped for non-JS repos)
    efs_node_modules = os.path.join(get_efs_dir(owner, repo), "node_modules")
    clone_node_modules = os.path.join(clone_dir, "node_modules")
    if os.path.exists(efs_node_modules) and not os.path.exists(clone_node_modules):
        os.symlink(efs_node_modules, clone_node_modules)

    return clone_dir
