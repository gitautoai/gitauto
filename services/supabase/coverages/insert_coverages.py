from schemas.supabase.types import CoveragesInsert
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_coverages(*, coverage_record: CoveragesInsert):
    result = supabase.table("coverages").insert(dict(coverage_record)).execute()
    logger.info(
        "insert_coverages: inserted platform=%s", coverage_record.get("platform")
    )
    return result.data
