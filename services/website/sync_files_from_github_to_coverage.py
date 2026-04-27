from schemas.supabase.types import CoveragesInsert
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.get_file_tree import get_file_tree
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.github.repositories.get_github_file_tree import get_github_file_tree
from services.github.token.get_installation_token import get_installation_access_token
from services.supabase.coverages.delete_stale_coverages import delete_stale_coverages
from services.supabase.coverages.upsert_coverages import upsert_coverages
from services.supabase.installations.get_installation_by_owner import (
    get_installation_by_owner,
)
from services.website.verify_api_key import verify_api_key
from utils.files.is_source_file import is_source_file
from utils.logging.logging_config import logger


def sync_files_from_github_to_coverage(
    owner: str,
    repo: str,
    branch: str,
    owner_id: int,
    repo_id: int,
    user_name: str,
    api_key: str | None,
):
    """Sync repository files from local clone to coverage database."""
    if api_key:
        logger.info("sync_files_from_github_to_coverage: verifying api_key")
        verify_api_key(api_key)

    logger.info("Starting sync for %s/%s branch=%s", owner, repo, branch)

    # Try local clone to /tmp first, fall back to GitHub API if clone not available
    installation = get_installation_by_owner(platform="github", owner_name=owner)
    if not installation:
        logger.warning("No installation found for %s, cannot fetch tree", owner)
        return

    token = get_installation_access_token(
        installation_id=installation["installation_id"]
    )
    clone_url = get_clone_url(owner, repo, token)
    clone_dir = get_clone_dir(owner, repo, pr_number=None)
    git_clone_to_tmp(clone_dir, clone_url, branch)
    tree_items = get_file_tree(clone_dir=clone_dir, ref=branch)

    # Fall back to GitHub API if clone to /tmp failed (e.g. user installed GitAuto and is redirected to the website file coverage page before the initial clone completes)
    if not tree_items:
        logger.info(
            "Local clone not available, using GitHub API for %s/%s", owner, repo
        )
        tree_items = get_github_file_tree(
            owner=owner, repo=repo, ref=branch, token=token
        )

    current_files = {
        item["path"]: item.get("size", 0)
        for item in tree_items
        if item["type"] == "blob" and is_source_file(item["path"])
    }

    logger.info("Fetched %d files from GitHub", len(current_files))

    # Upsert all files (handles both insert and update)
    if current_files:
        records: list[CoveragesInsert] = [
            CoveragesInsert(
                platform="github",
                owner_id=owner_id,
                repo_id=repo_id,
                full_path=path,
                file_size=size,
                branch_name=branch,
                level="file",
                created_by=user_name,
                updated_by=user_name,
                # SHAs/hash only set when quality is actually evaluated
                impl_blob_sha=None,
                test_blob_sha=None,
                checklist_hash=None,
                quality_checks=None,
            )
            for path, size in current_files.items()
        ]
        upsert_coverages(coverage_records=records)
        logger.info("Upserted %d coverage records", len(records))

    # Delete stale files (exist in DB but not in GitHub)
    # Skip if tree_items is empty — means we failed to read the repo, not safe to delete
    deleted_count = 0
    if tree_items:
        logger.info("Deleting stale coverages for %s/%s", owner, repo)
        deleted_count = delete_stale_coverages(
            platform="github",
            owner_id=owner_id,
            repo_id=repo_id,
            current_files=set(current_files.keys()),
        )
    else:
        logger.warning(
            "Skipping stale deletion for %s/%s — tree fetch may have failed and repo may actually have files, we accidentally deleted coverages before",
            owner,
            repo,
        )

    logger.info(
        "Sync completed: %d upserted, %d deleted", len(current_files), deleted_count
    )
