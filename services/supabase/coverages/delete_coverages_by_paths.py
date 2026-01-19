# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_coverages_by_paths(owner_id: int, repo_id: int, file_paths: list[str]):
    if not file_paths:
        return None

    result = (
        supabase.table("coverages")
        .delete()
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .in_("full_path", file_paths)
        .execute()
    )

    if result.data:
        logger.info(
            "Deleted %d stale coverage records for repo %d",
            len(result.data),
            repo_id,
        )

    return result.data
