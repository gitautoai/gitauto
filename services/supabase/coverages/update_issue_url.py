from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_issue_url(
    owner_id: int, repo_id: int, file_path: str, github_issue_url: str
):
    result = (
        supabase.table("coverages")
        .update({"github_issue_url": github_issue_url})
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("full_path", file_path)
        .execute()
    )

    return result.data
