from schemas.supabase.types import Repositories
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository(*, platform: Platform, owner_id: int, repo_id: int):
    # Query by both owner_id and repo_id because stale entries can exist after repo transfers.
    # When a repo is transferred (e.g., mohavro -> DashFin), the old owner's entry may remain while the new owner's entry is created. Without owner_id, we might return the wrong settings.
    result = (
        supabase.table("repositories")
        .select("*")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        logger.info("get_repository: found %s/%s/%s", platform, owner_id, repo_id)
        return Repositories(**result.data)

    logger.info("get_repository: no row for %s/%s/%s", platform, owner_id, repo_id)
    return None
