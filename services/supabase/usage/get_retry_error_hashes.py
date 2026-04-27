from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_retry_error_hashes(
    *, platform: Platform, owner_id: int, repo_id: int, pr_number: int
):
    # Get ALL usage records for this PR and aggregate hashes across all of them.
    response = (
        supabase.table("usage")
        .select("retry_error_hashes")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .not_.is_("retry_error_hashes", "null")
        .execute()
    )

    if not response.data:
        logger.info("No retry error hashes found for pr_number=%s", pr_number)
        return list[str]()

    records: list[dict[str, list[str] | None]] = response.data
    all_hashes: list[str] = []
    seen: set[str] = set()
    for record in records:
        hashes = record.get("retry_error_hashes")
        if not hashes:
            logger.info("get_retry_error_hashes: skipping record with empty hashes")
            continue
        for h in hashes:
            if h not in seen:
                logger.info("get_retry_error_hashes: appending hash %s", h)
                seen.add(h)
                all_hashes.append(h)

    logger.info(
        "Found %d unique retry error hashes for pr_number=%s",
        len(all_hashes),
        pr_number,
    )
    return all_hashes
