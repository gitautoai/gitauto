from typing import cast

from schemas.supabase.fastapi.schema_public_latest import RepositoriesBaseSchema
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_settings(repo_id: int):
    result = supabase.table("repositories").select("*").eq("repo_id", repo_id).execute()

    if result.data and result.data[0]:
        return cast(RepositoriesBaseSchema, result.data[0])

    return None
