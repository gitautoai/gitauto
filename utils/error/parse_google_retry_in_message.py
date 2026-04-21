import re

from utils.logging.logging_config import logger

# Matches "retry in 3.337s" or "retry in 3s" case-insensitively.
GOOGLE_RETRY_IN_RE = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


def parse_google_retry_in_message(err: Exception):
    """Return the retry delay in seconds extracted from a Gemini 429 message, or None.

    Unlike GitHub or Anthropic, the Gemini SDK surfaces its retry hint in the error message body rather than an HTTP header.
    The format is stable ("Please retry in 3.337071738s.") so a simple regex is enough.
    If the hint is absent (older API versions or certain quota classes), return None and let the caller fall back to another model.
    """
    match = GOOGLE_RETRY_IN_RE.search(str(err))
    if not match:
        logger.info(
            "parse_google_retry_in_message: google 429 message lacked 'retry in Ns' hint"
        )
        return None

    try:
        delay = float(match.group(1))
    except ValueError:
        logger.info(
            "parse_google_retry_in_message: google retry-in value %r unparseable",
            match.group(1),
        )
        return None

    logger.info("parse_google_retry_in_message: extracted %.2fs retry delay", delay)
    return delay
