from services.aws.s3.download_and_extract_dependency import download_and_extract_s3_deps
from services.git.copy_config_templates import copy_config_templates
from services.git.get_clone_url import get_clone_url
from services.git.git_checkout import git_checkout
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_fetch import git_fetch
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def clone_repo_and_install_dependencies(
    *,
    owner: str,
    repo: str,
    base_branch: str,
    pr_branch: str,
    token: str,
    clone_dir: str,
):
    clone_url = get_clone_url(owner, repo, token)

    # Step 1: Clone base branch (also sets git identity)
    git_clone_to_tmp(clone_dir, clone_url, base_branch)

    # Step 2: Fetch and checkout PR branch to work on. git_fetch returns False when the PR branch is no longer on the remote (stale webhook for a closed/merged PR); short-circuit so we don't run git_checkout against a missing FETCH_HEAD and trigger AGENT-3KC/3KD.
    if not git_fetch(clone_dir, clone_url, pr_branch):
        logger.info(
            "clone_repo_and_install_dependencies: skipping after stale fetch on %s",
            pr_branch,
        )
        return False
    git_checkout(clone_dir, pr_branch)

    # Step 3: Extract cached dependencies from S3
    download_and_extract_s3_deps(owner_name=owner, repo_name=repo, clone_dir=clone_dir)

    # Step 4: Copy config templates (e.g., .env.example → .env)
    copy_config_templates(clone_dir)
    logger.info("clone_repo_and_install_dependencies: completed for %s", clone_dir)
    return True
