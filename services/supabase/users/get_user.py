from typing import cast

from schemas.supabase.types import Users
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_user(user_id: int):
    data, _ = (
        supabase.table(table_name="users")
        .select("*")
        .eq(column="user_id", value=user_id)
        .execute()
    )
    if len(data[1]) > 0:
        user = cast(Users, data[1][0])
        return user

    return None
