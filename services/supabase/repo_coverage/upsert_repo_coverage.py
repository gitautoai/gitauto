from schemas.supabase.types import RepoCoverageInsert
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_repo_coverage(*, coverage_data: RepoCoverageInsert):
    result = supabase.table("repo_coverage").insert(dict(coverage_data)).execute()
    logger.info(
        "upsert_repo_coverage: inserted platform=%s", coverage_data.get("platform")
    )
    return result.data
