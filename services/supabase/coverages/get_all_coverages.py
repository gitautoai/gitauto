from schemas.supabase.types import Coverages
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

PAGE_SIZE = 1000


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_all_coverages(*, platform: Platform, owner_id: int, repo_id: int):
    all_records: list[Coverages] = []
    offset = 0

    while True:
        result = (
            supabase.table("coverages")
            .select("*")
            .eq("platform", platform)
            .eq("owner_id", owner_id)
            .eq("repo_id", repo_id)
            .eq("level", "file")
            .order("statement_coverage,file_size,full_path", desc=False)
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )

        if not result.data:
            logger.info("get_all_coverages: no more rows at offset=%s", offset)
            break

        all_records.extend(Coverages(**item) for item in result.data)

        if len(result.data) < PAGE_SIZE:
            logger.info(
                "get_all_coverages: short page, ending after %d records",
                len(all_records),
            )
            break

        offset += PAGE_SIZE

    logger.info(
        "get_all_coverages: returning %d records for %s/%s/%s",
        len(all_records),
        platform,
        owner_id,
        repo_id,
    )
    return all_records
