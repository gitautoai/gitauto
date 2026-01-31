from services.efs.copy_repo_from_efs_to_tmp import copy_repo_from_efs_to_tmp
from services.efs.get_efs_dir import get_efs_dir
from services.efs.extract_dependencies import extract_dependencies
from services.git.get_clone_url import get_clone_url
from services.git.git_checkout import git_checkout
from services.git.git_clone_to_efs import clone_tasks
from services.git.git_fetch import git_fetch
from services.git.git_reset import git_reset
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def prepare_repo_for_work(
    *,
    owner: str,
    repo: str,
    pr_branch: str,
    token: str,
    clone_dir: str,
):
    efs_dir = get_efs_dir(owner, repo)
    clone_url = get_clone_url(owner, repo, token)

    # Step 1: Wait for clone task (ensures EFS is cloned and up to date)
    clone_task = clone_tasks.get(efs_dir)
    if clone_task:
        logger.info("Waiting for clone task: %s", efs_dir)
        await clone_task

    # Step 2: Copy to tmp for PR-specific work
    copy_repo_from_efs_to_tmp(efs_dir, clone_dir)

    # Step 3: Extract dependencies from EFS tarball to clone_dir
    extract_dependencies(efs_dir, clone_dir)

    # Step 4: Fetch, checkout, and reset PR branch
    fetch_ok = await git_fetch(clone_dir, clone_url, pr_branch)
    if fetch_ok:
        await git_checkout(clone_dir, pr_branch)
        await git_reset(clone_dir)
