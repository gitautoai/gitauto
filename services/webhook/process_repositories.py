# Standard imports
import shutil
import tempfile

# Local imports
from services.git.clone_repo import clone_repo
from services.github.repositories.get_repository_stats import get_repository_stats
from services.github.types.repository import Repository
from services.supabase.repositories.upsert_repository import upsert_repository
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def process_repositories(
    owner_id: int,
    owner_name: str,
    repositories: list[Repository],
    token: str,
    user_id: int,
    user_name: str,
):
    for repo in repositories:
        repo_id = repo["id"]
        repo_name = repo["name"]

        # Always save the repository, with or without stats
        stats = {"file_count": 0, "blank_lines": 0, "comment_lines": 0, "code_lines": 0}

        # Create a temporary directory to clone the repository
        temp_dir = tempfile.mkdtemp()
        try:
            print(f"Cloning repository {repo_name} into {temp_dir}")
            clone_repo(
                owner=owner_name, repo=repo_name, token=token, target_dir=temp_dir
            )

            # Try to get repository stats, but don't fail if this doesn't work
            stats = get_repository_stats(local_path=temp_dir)
            print(f"Repository {repo_name} stats: {stats}")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

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
