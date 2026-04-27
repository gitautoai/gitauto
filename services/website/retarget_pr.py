from config import GITHUB_APP_GIT_EMAIL, GITHUB_APP_USER_ID, GITHUB_APP_USER_NAME
from constants.models import DEFAULT_FREE_MODEL
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.reset_pr_branch_to_new_base import reset_pr_branch_to_new_base
from services.github.pulls.get_pull_request import get_pull_request
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def retarget_pr(
    owner_name: str,
    repo_name: str,
    token: str,
    new_base_branch: str,
    pr_number: int,
    installation_id: int,
):
    """Retarget one PR to new base branch. Clones PR branch, then delegates to reset_pr_branch_to_new_base."""
    clone_url = get_clone_url(owner=owner_name, repo=repo_name, token=token)
    clone_dir = get_clone_dir(owner=owner_name, repo=repo_name, pr_number=pr_number)

    # Get PR data — provides pr_branch, repo metadata, and creator info
    pr = get_pull_request(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )
    pr_branch = pr["head"]["ref"]
    git_clone_to_tmp(clone_dir=clone_dir, clone_url=clone_url, branch=pr_branch)

    repo_data = pr["base"]["repo"]
    owner_data = repo_data["owner"]
    reviewers: list[str] = []
    github_urls: list[str] = []
    other_urls: list[str] = []
    pr_comments: list[str] = []
    base_args = BaseArgs(
        platform="github",
        owner_type=owner_data["type"],
        owner_id=owner_data["id"],
        owner=owner_name,
        repo_id=repo_data["id"],
        repo=repo_name,
        clone_url=clone_url,
        is_fork=repo_data["fork"],
        base_branch=new_base_branch,
        new_branch=pr_branch,
        installation_id=installation_id,
        token=token,
        sender_id=GITHUB_APP_USER_ID,
        sender_name=GITHUB_APP_USER_NAME,
        sender_email=GITHUB_APP_GIT_EMAIL,
        sender_display_name=GITHUB_APP_USER_NAME,
        reviewers=reviewers,
        github_urls=github_urls,
        other_urls=other_urls,
        clone_dir=clone_dir,
        pr_number=pr_number,
        pr_title=pr["title"],
        pr_body=pr["body"] or "",
        pr_comments=pr_comments,
        pr_creator=pr["user"]["login"],
        verify_consecutive_failures=0,
        quality_gate_fail_count=0,
        model_id=DEFAULT_FREE_MODEL,
        usage_id=0,
    )
    logger.info("Retargeting PR #%d to %s", pr_number, new_base_branch)
    reset_pr_branch_to_new_base(base_args=base_args, new_base_branch=new_base_branch)
