from schemas.supabase.types import Repositories
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_by_name(*, platform: Platform, owner_id: int, repo_name: str):
    result = (
        supabase.table("repositories")
        .select("*")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_name", repo_name)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        logger.info(
            "get_repository_by_name: found %s/%s/%s", platform, owner_id, repo_name
        )
        return Repositories(**result.data)

    logger.info(
        "get_repository_by_name: no row for %s/%s/%s", platform, owner_id, repo_name
    )
    return None
