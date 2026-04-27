from schemas.supabase.types import Coverages
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_coverages(
    *, platform: Platform, owner_id: int, repo_id: int, filenames: list[str]
):
    coverage_dict: dict[str, Coverages] = {}
    if not filenames:
        logger.info("get_coverages: no filenames, returning empty")
        return coverage_dict

    # Dynamic batching based on character count.
    # Empirically tested exact limit: 25,036 characters; using 20,000 as safe limit (80% of max).
    max_chars = 20000
    overhead = 100  # Query structure overhead

    batch = []
    current_chars = overhead

    for filename in filenames:
        # Each filename needs quotes and comma: "filename",
        filename_chars = len(filename) + 3

        if current_chars + filename_chars > max_chars and batch:
            logger.info("get_coverages: flushing batch of %d files", len(batch))
            # Process current batch
            result = (
                supabase.table("coverages")
                .select("*")
                .eq("platform", platform)
                .eq("owner_id", owner_id)
                .eq("repo_id", repo_id)
                .in_("full_path", batch)
                .execute()
            )

            if result.data:
                logger.info("get_coverages: batch returned %d rows", len(result.data))
                for item in result.data:
                    coverage_dict[item["full_path"]] = Coverages(**item)

            # Start new batch
            batch = [filename]
            current_chars = overhead + filename_chars
        else:
            logger.info("get_coverages: appending %s to batch", filename)
            batch.append(filename)
            current_chars += filename_chars

    # Process final batch
    if batch:
        logger.info("get_coverages: flushing final batch of %d files", len(batch))
        result = (
            supabase.table("coverages")
            .select("*")
            .eq("platform", platform)
            .eq("owner_id", owner_id)
            .eq("repo_id", repo_id)
            .in_("full_path", batch)
            .execute()
        )

        if result.data:
            logger.info("get_coverages: final batch returned %d rows", len(result.data))
            for item in result.data:
                coverage_dict[item["full_path"]] = Coverages(**item)

    logger.info(
        "get_coverages: total %d rows for %s/%s/%s",
        len(coverage_dict),
        platform,
        owner_id,
        repo_id,
    )
    return coverage_dict
