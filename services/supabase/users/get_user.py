from typing import cast

from schemas.supabase.types import Users
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_user(user_id: int):
    result = (
        supabase.table(table_name="users")
        .select("*")
        .eq(column="user_id", value=user_id)
        .execute()
    )
    if result.data:
        return cast(Users, result.data[0])
    return None
