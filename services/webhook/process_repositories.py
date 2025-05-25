# Standard imports
import shutil
import tempfile
from typing import Any

# Local imports
from services.git.clone_repo import clone_repo
from services.github.repositories.get_repository_stats import get_repository_stats
from services.supabase.repositories.upsert_repository import upsert_repository


def process_repositories(
    owner_id: int,
    owner_name: str,
    repositories: list[dict[str, Any]],
    token: str,
    user_id: int,
    user_name: str,
):
    for repo in repositories:
        repo_id = repo["id"]
        repo_name = repo["name"]

        # Create a temporary directory to clone the repository
        temp_dir = tempfile.mkdtemp()
        try:
            print(f"Cloning repository {repo_name} into {temp_dir}")
            clone_repo(
                owner=owner_name, repo=repo_name, token=token, target_dir=temp_dir
            )

            stats = get_repository_stats(local_path=temp_dir)
            print(f"Repository {repo_name} stats: {stats}")

            # Create repository record in Supabase
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
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
