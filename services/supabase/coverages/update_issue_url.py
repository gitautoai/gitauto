from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_issue_url(
    *,
    platform: Platform,
    owner_id: int,
    repo_id: int,
    file_path: str,
    github_issue_url: str,
    updated_by: str,
):
    result = (
        supabase.table("coverages")
        .update({"github_issue_url": github_issue_url, "updated_by": updated_by})
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("full_path", file_path)
        .execute()
    )
    logger.info("update_issue_url: %s/%s repo_id=%s", platform, file_path, repo_id)
    return result.data
