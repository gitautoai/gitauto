from schemas.supabase.types import RepositoryFeatures
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_features(*, platform: Platform, owner_id: int, repo_id: int):
    result = (
        supabase.table("repository_features")
        .select("*")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        logger.info(
            "get_repository_features: found for %s/%s/%s", platform, owner_id, repo_id
        )
        return RepositoryFeatures(**result.data)

    logger.info(
        "get_repository_features: no row for %s/%s/%s", platform, owner_id, repo_id
    )
    return None
