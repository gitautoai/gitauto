from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_usage(usage_id: int, **kwargs):
    """Update usage record with provided fields."""
    # Remove None values
    update_data = {k: v for k, v in kwargs.items() if v is not None}

    if not update_data:
        return

    supabase.table(table_name="usage").update(json=update_data).eq(
        column="id", value=usage_id
    ).execute()
