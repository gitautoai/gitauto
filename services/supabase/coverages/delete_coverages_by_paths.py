# Local imports
from constants.supabase import SUPABASE_BATCH_SIZE
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_coverages_by_paths(owner_id: int, repo_id: int, file_paths: list[str]):
    all_deleted: list[dict] = []

    if not file_paths:
        logger.info("No file paths provided for deletion in repo %d", repo_id)
        return all_deleted

    for i in range(0, len(file_paths), SUPABASE_BATCH_SIZE):
        batch = file_paths[i : i + SUPABASE_BATCH_SIZE]
        result = (
            supabase.table("coverages")
            .delete()
            .eq("owner_id", owner_id)
            .eq("repo_id", repo_id)
            .in_("full_path", batch)
            .execute()
        )
        if result.data:
            all_deleted.extend(result.data)
            logger.info(
                "Deleted %d records in batch for repo %d", len(result.data), repo_id
            )

    if all_deleted:
        logger.info(
            "Deleted %d stale coverage records for repo %d",
            len(all_deleted),
            repo_id,
        )

    return all_deleted
