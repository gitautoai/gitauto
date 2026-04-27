from postgrest.exceptions import APIError

from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def insert_check_suite(*, platform: Platform, check_suite_id: int):
    try:
        result = (
            supabase.table("check_suites")
            .insert({"platform": platform, "check_suite_id": check_suite_id})
            .execute()
        )

        if result.data and len(result.data) > 0:
            logger.info("insert_check_suite: %s/%s inserted", platform, check_suite_id)
            return True

        logger.info(
            "insert_check_suite: %s/%s no data returned (treating as duplicate)",
            platform,
            check_suite_id,
        )
        return False
    except APIError as e:
        if e.code == "23505":
            logger.info(
                "insert_check_suite: %s/%s duplicate (23505)", platform, check_suite_id
            )
            return False
        logger.warning(
            "insert_check_suite: %s/%s APIError code=%s, re-raising",
            platform,
            check_suite_id,
            e.code,
        )
        raise
