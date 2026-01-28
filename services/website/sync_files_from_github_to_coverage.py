from typing import cast

from schemas.supabase.types import CoveragesInsert
from services.github.trees.get_file_tree import get_file_tree
from services.supabase.coverages.delete_stale_coverages import delete_stale_coverages
from services.supabase.coverages.upsert_coverages import upsert_coverages
from services.website.verify_api_key import verify_api_key
from utils.files.is_code_file import is_code_file
from utils.files.is_migration_file import is_migration_file
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger


def sync_files_from_github_to_coverage(
    owner: str,
    repo: str,
    branch: str,
    token: str,
    owner_id: int,
    repo_id: int,
    user_name: str,
    api_key: str | None = None,
):
    """Sync repository files from GitHub to coverage database."""
    if api_key:
        verify_api_key(api_key)

    logger.info("Starting sync for %s/%s branch=%s", owner, repo, branch)

    # Fetch files from GitHub (only code files, excluding test and migration files)
    tree_items = get_file_tree(owner=owner, repo=repo, ref=branch, token=token)
    current_files = {
        item["path"]: item.get("size", 0)
        for item in tree_items
        if item["type"] == "blob"
        and is_code_file(item["path"])
        and not is_test_file(item["path"])
        and not is_migration_file(item["path"])
    }

    logger.info("Fetched %d files from GitHub", len(current_files))

    # Upsert all files (handles both insert and update)
    if current_files:
        records = cast(
            list[CoveragesInsert],
            [
                {
                    "owner_id": owner_id,
                    "repo_id": repo_id,
                    "full_path": path,
                    "file_size": size,
                    "branch_name": branch,
                    "level": "file",
                    "created_by": user_name,
                    "updated_by": user_name,
                }
                for path, size in current_files.items()
            ],
        )
        upsert_coverages(records)
        logger.info("Upserted %d coverage records", len(records))

    # Delete stale files (exist in DB but not in GitHub)
    deleted_count = delete_stale_coverages(
        owner_id=owner_id,
        repo_id=repo_id,
        current_files=set(current_files.keys()),
    )

    logger.info(
        "Sync completed: %d upserted, %d deleted", len(current_files), deleted_count
    )
