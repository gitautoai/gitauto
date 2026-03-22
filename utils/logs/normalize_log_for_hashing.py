import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def normalize_log_for_hashing(log: str):
    # Strip 40-char hex strings (git commit SHAs)
    normalized = re.sub(r"\b[0-9a-f]{40}\b", "<SHA>", log)

    # Strip 7-char abbreviated SHAs that appear after @ or in parentheses (e.g. "abc1234")
    normalized = re.sub(r"(?<=@)[0-9a-f]{7}\b", "<SHORT_SHA>", normalized)

    # Strip 24-char hex strings (MongoDB ObjectIds)
    normalized = re.sub(r"\b[0-9a-f]{24}\b", "<OID>", normalized)

    # Strip ISO 8601 timestamps (e.g. "2026-03-20T15:58:04.7920475Z")
    normalized = re.sub(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\.\d]*Z?", "<TIMESTAMP>", normalized
    )
    return normalized
