# Standard imports
import json

# Local imports
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_quality_checks(
    *,
    platform: Platform,
    owner_id: int,
    repo_id: int,
    file_path: str,
    impl_blob_sha: str,
    test_blob_sha: str | None,
    checklist_hash: str,
    quality_checks: dict[str, dict[str, dict[str, str]]],
    updated_by: str,
):
    result = (
        supabase.table("coverages")
        .update(
            {
                "impl_blob_sha": impl_blob_sha,
                "test_blob_sha": test_blob_sha,
                "checklist_hash": checklist_hash,
                "quality_checks": json.dumps(quality_checks),
                "updated_by": updated_by,
            }
        )
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("full_path", file_path)
        .execute()
    )
    logger.info("update_quality_checks: %s/%s repo_id=%s", platform, file_path, repo_id)
    return result.data
