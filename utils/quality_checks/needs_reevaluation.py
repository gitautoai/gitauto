# Local imports
from schemas.supabase.types import Coverages
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=True, raise_on_error=False)
def needs_quality_reevaluation(
    coverage: Coverages,
    current_impl_sha: str,
    current_test_sha: str | None,
    current_checklist_hash: str,
):
    if not coverage.get("quality_checks"):
        logger.info(
            "Never evaluated: quality_checks is NULL for %s", coverage["full_path"]
        )
        return True

    stored_impl_sha = coverage.get("impl_blob_sha")
    if stored_impl_sha != current_impl_sha:
        logger.info(
            "Impl changed, tests may not cover new code: impl_blob_sha for %s (%s -> %s)",
            coverage["full_path"],
            stored_impl_sha,
            current_impl_sha,
        )
        return True

    stored_test_sha = coverage.get("test_blob_sha")
    if stored_test_sha != current_test_sha:
        logger.info(
            "Tests updated, verify they still pass quality bar: test_blob_sha for %s (%s -> %s)",
            coverage["full_path"],
            stored_test_sha,
            current_test_sha,
        )
        return True

    stored_checklist_hash = coverage.get("checklist_hash")
    if stored_checklist_hash != current_checklist_hash:
        logger.info(
            "New checks added to checklist, need evaluation: checklist_hash for %s (%s -> %s)",
            coverage["full_path"],
            stored_checklist_hash,
            current_checklist_hash,
        )
        return True

    logger.info("No re-eval needed for %s", coverage["full_path"])
    return False
