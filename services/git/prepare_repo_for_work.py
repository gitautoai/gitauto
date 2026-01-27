import os

from services.efs.copy_repo_from_efs_to_tmp import copy_repo_from_efs_to_tmp
from services.efs.get_efs_dir import get_efs_dir
from services.efs.symlink_dependencies import symlink_dependencies
from services.git.get_clone_url import get_clone_url
from services.git.git_checkout import git_checkout
from services.git.git_clone_to_efs import git_clone_to_efs
from services.git.git_fetch import git_fetch
from services.git.git_reset import git_reset
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def prepare_repo_for_work(
    *,
    owner: str,
    repo: str,
    base_branch: str,
    pr_branch: str,
    token: str,
    clone_dir: str,
):
    efs_dir = get_efs_dir(owner, repo)
    efs_git_dir = os.path.join(efs_dir, ".git")
    clone_url = get_clone_url(owner, repo, token)

    # Step 1: Clone or update EFS with base branch
    if os.path.exists(efs_git_dir):
        logger.info("EFS clone exists, updating: %s", efs_dir)
        fetch_ok = await git_fetch(efs_dir, clone_url, base_branch)
        if fetch_ok:
            await git_reset(efs_dir)
    else:
        logger.info("No EFS clone, creating: %s", efs_dir)
        await git_clone_to_efs(efs_dir, clone_url, base_branch)

    # Step 2: Copy to tmp for PR-specific work
    copy_repo_from_efs_to_tmp(efs_dir, clone_dir)

    # Step 3: Symlink dependencies (node_modules, venv, etc.) to avoid re-installing
    symlink_dependencies(efs_dir, clone_dir)

    # Step 4: Fetch, checkout, and reset PR branch
    fetch_ok = await git_fetch(clone_dir, clone_url, pr_branch)
    if fetch_ok:
        await git_checkout(clone_dir, pr_branch)
        await git_reset(clone_dir)
