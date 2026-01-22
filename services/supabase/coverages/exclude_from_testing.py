from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def exclude_from_testing(
    owner_id: int,
    repo_id: int,
    full_path: str,
    branch_name: str,
    exclusion_reason: str,
    updated_by: str,
):
    result = (
        supabase.table("coverages")
        .upsert(
            {
                "owner_id": owner_id,
                "repo_id": repo_id,
                "full_path": full_path,
                "branch_name": branch_name,
                "level": "file",
                "created_by": updated_by,
                "is_excluded_from_testing": True,
                "exclusion_reason": exclusion_reason,
                "updated_by": updated_by,
            },
            on_conflict="repo_id,full_path",
            default_to_null=False,
        )
        .execute()
    )
    return result.data
