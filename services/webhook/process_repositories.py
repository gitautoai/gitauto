# Standard imports
import os

# Local imports
from services.efs.get_efs_dir import get_efs_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import git_clone_to_efs
from services.git.git_fetch import git_fetch
from services.git.git_reset import git_reset
from services.github.branches.get_default_branch import get_default_branch
from services.github.repositories.get_repository_stats import get_repository_stats
from services.github.types.owner import OwnerType
from services.github.types.repository import RepositoryAddedOrRemoved
from services.aws.run_install_via_ssm import run_install_via_ssm
from services.supabase.repositories.upsert_repository import upsert_repository
from services.website.sync_files_from_github_to_coverage import (
    sync_files_from_github_to_coverage,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
async def process_repositories(
    owner_id: int,
    owner_name: str,
    owner_type: OwnerType,
    repositories: list[RepositoryAddedOrRemoved],
    token: str,
    user_id: int,
    user_name: str,
):
    for repo in repositories:
        repo_id = repo["id"]
        repo_name = repo["name"]

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

        default_branch, is_empty = get_default_branch(
            owner=owner_name, repo=repo_name, token=token
        )

        # Empty repos (size=0) have no commits - skip cloning
        if is_empty:
            logger.info(
                "Repository %s/%s is empty, skipping clone", owner_name, repo_name
            )
            continue

        # Clone or update EFS (reusable for future issue/PR work)
        efs_dir = get_efs_dir(owner_name, repo_name)
        efs_git_dir = os.path.join(efs_dir, ".git")
        clone_url = get_clone_url(owner_name, repo_name, token)

        if os.path.exists(efs_git_dir):
            logger.info("EFS clone exists, updating: %s", efs_dir)
            fetch_ok = await git_fetch(efs_dir, clone_url, default_branch)
            if fetch_ok:
                await git_reset(efs_dir)
        else:
            logger.info("No EFS clone, creating: %s", efs_dir)
            await git_clone_to_efs(efs_dir, clone_url, default_branch)

        # Start package install on EC2 (fire-and-forget)
        run_install_via_ssm(efs_dir, owner_id)

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

        # Sync files to coverage database
        sync_files_from_github_to_coverage(
            owner=owner_name,
            repo=repo_name,
            branch=default_branch,
            token=token,
            owner_id=owner_id,
            repo_id=repo_id,
            user_name=user_name,
        )
