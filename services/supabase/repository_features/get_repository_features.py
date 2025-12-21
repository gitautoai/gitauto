from typing import cast

from schemas.supabase.types import RepositoryFeatures
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_features(repo_id: int):
    result = (
        supabase.table("repository_features")
        .select("*")
        .eq("repo_id", repo_id)
        .execute()
    )

    if result.data and result.data[0]:
        return cast(RepositoryFeatures, result.data[0])
    return None
