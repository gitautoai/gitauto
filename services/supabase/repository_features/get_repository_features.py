from typing import cast

from schemas.supabase.types import RepositoryFeatures
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_features(owner_id: int, repo_id: int):
    result = (
        supabase.table("repository_features")
        .select("*")
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        return cast(RepositoryFeatures, result.data)
    return None
