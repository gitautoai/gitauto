from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_usage(
    usage_id: int,
    token_input: int,
    token_output: int,
    total_seconds: int,
    is_completed: bool = True,
    pr_number: int | None = None,
):
    """Add agent information to usage record and set is_completed to True."""
    supabase.table(table_name="usage").update(
        json={
            "is_completed": is_completed,
            "pr_number": pr_number,
            "token_input": token_input,
            "token_output": token_output,
            "total_seconds": total_seconds,
        }
    ).eq(column="id", value=usage_id).execute()
