from services.supabase.coverages.delete_coverages_by_paths import (
    delete_coverages_by_paths,
)
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.types.base_args import Platform
from utils.logging.logging_config import logger


def delete_stale_coverages(
    *,
    platform: Platform,
    owner_id: int,
    repo_id: int,
    current_files: set[str],
):
    """Delete coverage records for files that no longer exist in the repository."""
    all_records = get_all_coverages(
        platform=platform, owner_id=owner_id, repo_id=repo_id
    )
    stale_paths = [
        record["full_path"]
        for record in all_records
        if record["full_path"] not in current_files
    ]

    if stale_paths:
        delete_coverages_by_paths(
            platform=platform,
            owner_id=owner_id,
            repo_id=repo_id,
            file_paths=stale_paths,
        )
        logger.info("Deleted %d stale coverage records", len(stale_paths))

    logger.info(
        "delete_stale_coverages: %d stale paths for repo %s", len(stale_paths), repo_id
    )
    return len(stale_paths)
