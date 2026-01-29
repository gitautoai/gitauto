from typing import cast

from schemas.supabase.types import Repositories
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_by_name(owner_id: int, repo_name: str):
    result = (
        supabase.table("repositories")
        .select("*")
        .eq("owner_id", owner_id)
        .eq("repo_name", repo_name)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        return cast(Repositories, result.data)

    return None
