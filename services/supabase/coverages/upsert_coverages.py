# Local imports
from schemas.supabase.types import CoveragesInsert
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_coverages(*, coverage_records: list[CoveragesInsert]):
    if not coverage_records:
        logger.info("upsert_coverages: no records, skipping")
        return None

    result = (
        supabase.table("coverages")
        .upsert(
            [dict(r) for r in coverage_records],
            on_conflict="platform,repo_id,full_path",
            default_to_null=False,
        )
        .execute()
    )
    logger.info("upsert_coverages: upserted %d records", len(coverage_records))
    return result.data
