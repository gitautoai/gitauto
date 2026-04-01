# Path-based exclusion reasons — files that can never be unit tested regardless of content.
# LLM-evaluated exclusions use free-text reasons and are re-evaluated when impl changes.
REASON_NOT_CODE = "not code file"
REASON_DEPENDENCY = "dependency file"
REASON_TEST = "test file"
REASON_CONFIG = "config file"
REASON_TYPE = "type file"
REASON_MIGRATION = "migration file"
REASON_EMPTY = "empty file"
REASON_ONLY_EXPORTS = "only exports"

PERMANENT_EXCLUSION_REASONS = frozenset(
    {
        REASON_NOT_CODE,
        REASON_DEPENDENCY,
        REASON_TEST,
        REASON_CONFIG,
        REASON_TYPE,
        REASON_MIGRATION,
        REASON_EMPTY,
        REASON_ONLY_EXPORTS,
    }
)
