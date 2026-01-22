# Standard imports
import os

# Local imports
from services.efs.get_efs_dir import get_efs_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import git_clone_to_efs
from services.git.git_pull import git_pull
from services.github.branches.get_default_branch import get_default_branch
from services.github.repositories.get_repository_stats import get_repository_stats
from services.github.types.repository import RepositoryAddedOrRemoved
from services.supabase.repositories.upsert_repository import upsert_repository
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
async def process_repositories(
    owner_id: int,
    owner_name: str,
    repositories: list[RepositoryAddedOrRemoved],
    token: str,
    user_id: int,
    user_name: str,
):
    for repo in repositories:
        repo_id = repo["id"]
        repo_name = repo["name"]
        default_branch, latest_commit_sha = get_default_branch(
            owner=owner_name, repo=repo_name, token=token
        )

        # Always save the repository, with or without stats
        stats = {"file_count": 0, "blank_lines": 0, "comment_lines": 0, "code_lines": 0}

        # Empty repos (no commits) have empty commit SHA - skip cloning
        if not latest_commit_sha:
            logger.info(
                "Repository %s/%s is empty, skipping clone", owner_name, repo_name
            )
        else:
            # Clone or update EFS (reusable for future issue/PR work)
            efs_dir = get_efs_dir(owner_name, repo_name)
            efs_git_dir = os.path.join(efs_dir, ".git")
            clone_url = get_clone_url(owner_name, repo_name, token)

            if os.path.exists(efs_git_dir):
                logger.info("EFS clone exists, updating: %s", efs_dir)
                await git_pull(efs_dir, clone_url, default_branch)
            else:
                logger.info("No EFS clone, creating: %s", efs_dir)
                await git_clone_to_efs(efs_dir, clone_url, default_branch)

            # Get stats directly from EFS (no need to copy to /tmp)
            stats = get_repository_stats(local_path=efs_dir)
            logger.info("Repository %s stats: %s", repo_name, stats)

        # Always create repository record in Supabase, even if stats failed
        upsert_repository(
            owner_id=owner_id,
            owner_name=owner_name,
            repo_id=repo_id,
            repo_name=repo_name,
            user_id=user_id,
            user_name=user_name,
            file_count=stats["file_count"],
            blank_lines=stats["blank_lines"],
            comment_lines=stats["comment_lines"],
            code_lines=stats["code_lines"],
        )
