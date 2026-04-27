from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_usage_by_pr(*, platform: Platform, owner_id: int, repo_id: int, pr_number: int):
    result = (
        supabase.table("usage")
        .select("id")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .execute()
    )
    logger.info(
        "get_usage_by_pr: %d rows for %s/%s/%s#%s",
        len(result.data),
        platform,
        owner_id,
        repo_id,
        pr_number,
    )
    return result.data
