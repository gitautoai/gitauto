from constants.models import (
    DEFAULT_FREE_MODEL,
    DEFAULT_PAID_MODEL,
    MODEL_ID_BY_VALUE,
    ModelId,
    USER_SELECTABLE_MODELS,
)
from schemas.supabase.types import Repositories
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=DEFAULT_FREE_MODEL, raise_on_error=False)
def get_preferred_model(
    repo_settings: Repositories | None,
    is_paid: bool,
):
    """Determine which model to use based on repo settings and billing tier."""
    # 1. Read preferred_model from repo settings (DB text -> ModelId validation)
    raw_preferred = repo_settings.get("preferred_model") if repo_settings else None
    preferred: ModelId | None = None
    if raw_preferred:
        preferred = MODEL_ID_BY_VALUE.get(raw_preferred)
        if not preferred:
            logger.warning("Unknown preferred model %s, ignoring", raw_preferred)

    # Reject non-selectable models (e.g. fallback-only like Opus 4.5)
    if preferred and preferred not in USER_SELECTABLE_MODELS:
        logger.warning("Model %s is not user-selectable, ignoring", preferred)
        preferred = None

    # 2. DB has a valid model set → use it regardless of billing tier
    if preferred:
        logger.info("Using DB preferred model %s", preferred)
        return preferred

    # 3. No preference set → default based on billing tier
    if is_paid:
        logger.info("Paid user, no preference, using %s", DEFAULT_PAID_MODEL)
        return DEFAULT_PAID_MODEL

    logger.info("Free user, no preference, using %s", DEFAULT_FREE_MODEL)
    return DEFAULT_FREE_MODEL
