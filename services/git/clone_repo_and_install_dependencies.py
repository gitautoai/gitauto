from services.aws.s3.download_and_extract_dependency import download_and_extract_s3_deps
from services.git.copy_config_templates import copy_config_templates
from services.git.get_clone_url import get_clone_url
from services.git.git_checkout import git_checkout
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_fetch import git_fetch
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
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

    # Step 1: Clone base branch so it's available locally
    git_clone_to_tmp(clone_dir, clone_url, base_branch)

    # Step 2: Fetch and checkout PR branch to work on
    git_fetch(clone_dir, clone_url, pr_branch)
    git_checkout(clone_dir, pr_branch)

    # Step 3: Extract dependencies from S3 tarball to clone_dir
    download_and_extract_s3_deps(owner, repo, clone_dir)

    # Step 4: Copy config templates (e.g., .env.example → .env)
    copy_config_templates(clone_dir)
