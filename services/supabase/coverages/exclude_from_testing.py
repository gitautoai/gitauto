from schemas.supabase.types import Coverages, CoveragesInsert
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def exclude_from_testing(
    *,
    platform: Platform,
    owner_id: int,
    repo_id: int,
    full_path: str,
    branch_name: str,
    exclusion_reason: str,
    updated_by: str,
    impl_blob_sha: str | None,
):
    data: CoveragesInsert = {
        "platform": platform,
        "owner_id": owner_id,
        "repo_id": repo_id,
        "full_path": full_path,
        "branch_name": branch_name,
        "level": "file",
        "created_by": updated_by,
        "is_excluded_from_testing": True,
        "exclusion_reason": exclusion_reason,
        "updated_by": updated_by,
        "impl_blob_sha": impl_blob_sha,
    }
    result = (
        supabase.table("coverages")
        .upsert(
            dict(data), on_conflict="platform,repo_id,full_path", default_to_null=False
        )
        .execute()
    )
    rows: list[Coverages] = result.data
    logger.info(
        "exclude_from_testing: %s/%s platform=%s reason=%s",
        repo_id,
        full_path,
        platform,
        exclusion_reason,
    )
    return rows
