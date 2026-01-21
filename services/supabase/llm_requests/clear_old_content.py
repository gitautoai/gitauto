from datetime import datetime, timedelta

from postgrest.exceptions import APIError

from services.supabase.client import supabase

BATCH_SIZE = 1000


def clear_old_content(retention_days: int = 14):
    cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
    total_cleared = 0

    try:
        while True:
            batch = (
                supabase.table("llm_requests")
                .select("id")
                .lt("created_at", cutoff_date)
                .neq("input_content", "")
                .limit(BATCH_SIZE)
                .execute()
            )

            if not batch.data:
                break

            ids = [row["id"] for row in batch.data]

            supabase.table("llm_requests").update(
                {"input_content": "", "output_content": ""}
            ).in_("id", ids).execute()

            total_cleared += len(ids)

            if len(ids) < BATCH_SIZE:
                break

        return total_cleared
    except APIError as err:
        print(f"Error clearing old content: {err}")  # noqa: T201
        return None
