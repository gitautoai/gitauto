from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_repository(
    owner_id: int, repo_id: int, updated_by: str = "system", **kwargs
):
    update_data = {"updated_by": updated_by, **kwargs}

    update_result = (
        supabase.table("repositories")
        .update(update_data)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .execute()
    )

    return update_result.data[0] if update_result.data else None
