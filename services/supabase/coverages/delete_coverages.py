from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_coverages(repo_id: int, exclude_paths: list[str] = None):
    query = supabase.table("coverages").delete().eq("repo_id", repo_id)

    if exclude_paths:
        query = query.not_.in_("full_path", exclude_paths)

    return query.execute()
