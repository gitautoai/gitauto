# Standard imports
import json

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_quality_checks(
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
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("full_path", file_path)
        .execute()
    )

    return result.data
