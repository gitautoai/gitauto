from datetime import datetime, timedelta

from constants.supabase import SUPABASE_BATCH_SIZE
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def clear_old_error_logs(retention_days: int = 14):
    cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
    total_cleared = 0

    while True:
        batch = (
            supabase.table("usage")
            .select("id")
            .lt("created_at", cutoff_date)
            .neq("original_error_log", "")
            .limit(SUPABASE_BATCH_SIZE)
            .execute()
        )

        if not batch.data:
            break

        ids = [row["id"] for row in batch.data]

        supabase.table("usage").update(
            {"original_error_log": "", "minimized_error_log": ""}
        ).in_("id", ids).execute()

        total_cleared += len(ids)

        if len(ids) < SUPABASE_BATCH_SIZE:
            break

    return total_cleared
