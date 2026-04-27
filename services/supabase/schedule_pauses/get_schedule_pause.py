# Standard imports
from dataclasses import dataclass
from datetime import datetime, timezone

# Local imports
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class SchedulePause:
    pause_start: str
    pause_end: str


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_schedule_pause(*, platform: Platform, owner_id: int, repo_id: int):
    now_utc = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("schedule_pauses")
        .select("id, pause_start, pause_end")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .lte("pause_start", now_utc)
        .gte("pause_end", now_utc)
        .limit(1)
        .execute()
    )

    if result and result.data:
        row = result.data[0]
        pause = SchedulePause(
            pause_start=row["pause_start"], pause_end=row["pause_end"]
        )
        logger.info(
            "Schedule paused for owner_id=%s, repo_id=%s from %s to %s (pause id: %s)",
            owner_id,
            repo_id,
            pause.pause_start,
            pause.pause_end,
            row["id"],
        )
        return pause

    logger.info(
        "get_schedule_pause: no active pause for %s/%s/%s", platform, owner_id, repo_id
    )
    return None
