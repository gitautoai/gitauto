# Standard imports
import os

# Local imports
from schemas.supabase.types import OwnerType
from services.aws.run_install_via_codebuild import run_install_via_codebuild
from services.efs.get_efs_dir import get_efs_dir
from services.git.create_remote_branch import create_remote_branch
from services.git.delete_remote_branch import delete_remote_branch
from services.git.get_clone_url import get_clone_url
from services.git.get_default_branch import get_default_branch
from services.git.get_latest_remote_commit_sha import get_latest_remote_commit_sha
from services.git.git_clone_to_efs import git_clone_to_efs
from services.git.git_fetch import git_fetch
from services.git.git_reset import git_reset
from services.github.branches.is_repo_archived import is_repo_archived
from services.github.pulls.create_pull_request import create_pull_request
from services.github.pulls.has_open_pull_request_by_title import (
    has_open_pull_request_by_title,
)
from services.github.repositories.is_repo_forked import is_repo_forked
from services.github.token.get_installation_token import get_installation_access_token
from services.node.detect_package_manager import detect_package_manager
from services.node.ensure_jest_uses_tsconfig_for_tests import (
    ensure_jest_uses_tsconfig_for_tests,
)
from services.node.ensure_tsconfig_relaxed_for_tests import (
    ensure_tsconfig_relaxed_for_tests,
)
from services.supabase.repositories.upsert_repository import upsert_repository
from services.types.base_args import BaseArgs
from services.website.sync_files_from_github_to_coverage import (
    sync_files_from_github_to_coverage,
)
from utils.build_setup_pr_body import (
    SETUP_PR_TITLE,
    build_setup_pr_body,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.get_repository_stats import get_repository_stats
from utils.generate_branch_name import generate_branch_name
from utils.logging.logging_config import logger, set_owner_repo


@handle_exceptions(raise_on_error=False)
def setup_installed_repository(
    owner_id: int,
    owner_name: str,
    owner_type: OwnerType,
    repo_id: int,
    repo_name: str,
    installation_id: int,
    user_id: int,
    user_name: str,
    sender_email: str | None,
    sender_display_name: str,
):
    """Process a single repository: clone, sync, create setup PR."""
    set_owner_repo(owner_name, repo_name)

    # Insert repository first (without stats to avoid overwriting existing)
    upsert_repository(
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repo_id=repo_id,
        repo_name=repo_name,
        user_id=user_id,
        user_name=user_name,
    )

    # Get fresh token for this invocation
    token = get_installation_access_token(installation_id=installation_id)
    if is_repo_archived(owner=owner_name, repo=repo_name, token=token):
        logger.info("Repository %s/%s is archived, skipping", owner_name, repo_name)
        return

    clone_url = get_clone_url(owner_name, repo_name, token)
    default_branch = get_default_branch(clone_url=clone_url)

    # Empty repos have no commits - skip cloning
    if not default_branch:
        logger.info("Repository %s/%s is empty, skipping clone", owner_name, repo_name)
        return

    # Clone or update EFS (reusable for future PR work)
    efs_dir = get_efs_dir(owner_name, repo_name)
    efs_git_dir = os.path.join(efs_dir, ".git")

    if os.path.exists(efs_git_dir):
        logger.info("EFS clone exists, updating: %s", efs_dir)
        fetch_ok = git_fetch(efs_dir, clone_url, default_branch)
        if fetch_ok:
            git_reset(efs_dir)
    else:
        logger.info("No EFS clone, creating: %s", efs_dir)
        git_clone_to_efs(efs_dir, clone_url, default_branch)

    # Start package install via CodeBuild (fire-and-forget) for Node projects
    pkg_manager, lock_file, _ = detect_package_manager(efs_dir)
    if lock_file:
        run_install_via_codebuild(efs_dir, owner_id, pkg_manager)

    # Get stats and update repository
    stats = get_repository_stats(local_path=efs_dir)
    logger.info("Repository %s stats: %s", repo_name, stats)
    upsert_repository(
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repo_id=repo_id,
        repo_name=repo_name,
        user_id=user_id,
        user_name=user_name,
        file_count=stats["file_count"],
        blank_lines=stats["blank_lines"],
        comment_lines=stats["comment_lines"],
        code_lines=stats["code_lines"],
    )

    # Sync files to coverage database (generates its own token for GitHub API fallback)
    sync_files_from_github_to_coverage(
        owner=owner_name,
        repo=repo_name,
        branch=default_branch,
        owner_id=owner_id,
        repo_id=repo_id,
        user_name=user_name,
        api_key=None,
    )

    # Check if setup PR already exists before creating a new one
    if has_open_pull_request_by_title(
        owner=owner_name, repo=repo_name, token=token, title=SETUP_PR_TITLE
    ):
        logger.info(
            "Setup PR already exists for %s/%s, skipping", owner_name, repo_name
        )
        return

    # Create GitAuto setup PR with any necessary configuration
    new_branch = generate_branch_name(trigger="setup")

    base_args: BaseArgs = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": clone_url,
        "is_fork": is_repo_forked(owner=owner_name, repo=repo_name, token=token),
        "base_branch": default_branch,
        "new_branch": new_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": user_id,
        "sender_name": user_name,
        "sender_email": sender_email,
        "sender_display_name": sender_display_name,
        "reviewers": [user_name] if user_name and "[bot]" not in user_name else [],
        "github_urls": [],
        "other_urls": [],
        "clone_dir": efs_dir,
        "pr_number": 0,
        "pr_title": SETUP_PR_TITLE,
        "pr_body": "",
        "pr_comments": [],
        "pr_creator": user_name,
    }

    sha = get_latest_remote_commit_sha(clone_url=clone_url, base_args=base_args)
    create_remote_branch(sha=sha, base_args=base_args)

    # Run setup tasks - each adds commits if needed
    changes: list[str] = []

    root_files = [
        f for f in os.listdir(efs_dir) if os.path.isfile(os.path.join(efs_dir, f))
    ]

    tsconfig_path, tsconfig_status = ensure_tsconfig_relaxed_for_tests(
        root_files=root_files,
        base_args=base_args,
    )
    if tsconfig_status:
        changes.append(f"{tsconfig_status.capitalize()} {tsconfig_path}")

    if tsconfig_path:
        jest_path, jest_status = ensure_jest_uses_tsconfig_for_tests(
            root_files=root_files,
            base_args=base_args,
            tsconfig_path=tsconfig_path,
        )
        if jest_status:
            changes.append(f"{jest_status.capitalize()} {jest_path}")

    if not changes:
        logger.info("No setup changes needed, deleting branch")
        delete_remote_branch(base_args=base_args)
        return

    _pr_url, pr_number = create_pull_request(
        body=build_setup_pr_body(changes),
        title=SETUP_PR_TITLE,
        base_args=base_args,
    )

    logger.info("Created setup PR %s/%s#%d", owner_name, repo_name, pr_number)
