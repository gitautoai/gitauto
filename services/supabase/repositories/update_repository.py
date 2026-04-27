from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_repository(
    *,
    platform: Platform,
    owner_id: int,
    repo_id: int,
    updated_by: str = "system",
    **kwargs,
):
    update_data = {"updated_by": updated_by, **kwargs}

    update_result = (
        supabase.table("repositories")
        .update(update_data)
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .execute()
    )

    row = update_result.data[0] if update_result.data else None
    logger.info(
        "update_repository: %s repo_id=%s platform=%s",
        "updated" if row else "no-op",
        repo_id,
        platform,
    )
    return row
