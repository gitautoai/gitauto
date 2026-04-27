from constants.triggers import Trigger
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_usage_id_by_pr_and_trigger(
    *,
    platform: Platform,
    installation_id: int,
    repo_id: int,
    pr_number: int,
    trigger: Trigger,
):
    result = (
        supabase.table(table_name="usage")
        .select("id")
        .eq(column="platform", value=platform)
        .eq(column="installation_id", value=installation_id)
        .eq(column="repo_id", value=repo_id)
        .eq(column="pr_number", value=pr_number)
        .eq(column="trigger", value=trigger)
        .limit(size=1)
        .execute()
    )
    if not result.data:
        logger.info(
            "No usage row for repo_id=%s pr=%s trigger=%s",
            repo_id,
            pr_number,
            trigger,
        )
        return None
    usage_id = int(result.data[0]["id"])
    logger.info(
        "Found usage_id=%s for repo_id=%s pr=%s trigger=%s",
        usage_id,
        repo_id,
        pr_number,
        trigger,
    )
    return usage_id
