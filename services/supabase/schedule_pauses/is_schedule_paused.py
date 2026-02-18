# Standard imports
from datetime import datetime, timezone

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_schedule_paused(owner_id: int, repo_id: int):
    """Check if a schedule is currently paused for a given owner and repo."""
    now_utc = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("schedule_pauses")
        .select("id")
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .lte("pause_start", now_utc)
        .gte("pause_end", now_utc)
        .limit(1)
        .execute()
    )

    if result and result.data:
        logger.info(
            "Schedule paused for owner_id=%s, repo_id=%s (pause id: %s)",
            owner_id,
            repo_id,
            result.data[0]["id"],
        )
        return True

    return False
