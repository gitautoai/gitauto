from datetime import datetime, timedelta
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def clear_old_content(retention_days: int = 14):
    cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()

    result = (
        supabase.table("llm_requests")
        .update({"input_content": "", "output_content": ""})
        .lt("created_at", cutoff_date)
        .execute()
    )

    return result.data if result.data else None
