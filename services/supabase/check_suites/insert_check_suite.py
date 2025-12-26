from postgrest.exceptions import APIError

from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def insert_check_suite(check_suite_id: int):
    try:
        result = (
            supabase.table("check_suites")
            .insert({"check_suite_id": check_suite_id})
            .execute()
        )

        if result.data and len(result.data) > 0:
            return True

        return False
    except APIError as e:
        if e.code == "23505":
            return False
        raise
