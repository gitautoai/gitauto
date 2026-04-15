import re

from utils.error.handle_exceptions import handle_exceptions

# MongoDB config patterns that appear during test setup (MongoMemoryServer, connection logs)
MONGO_CONFIG_PREFIXES = (
    "Using default value ",
    "Connected to MongoDB",
    "[EMFILE ",
    "*** new process",
    "stage is undefined",
)

# Test seed data patterns from Foxquilt test infrastructure
SEED_DATA_PREFIXES = (
    "E&C:",
    "inserted ",
)

# Business data logged during test setup (policy/invoice/quote creation)
BUSINESS_DATA_RE = re.compile(
    r"^(policy number:|invoice number:|quoteNumber:|getIds for )"
)

# Migration file entries in array dumps: '20220505134722-manual-cancellation-P202203047MQ1YA.js',
MIGRATION_FILE_RE = re.compile(r"^'\d{8,14}-.+\.js',?$")

# AWS SDK error metadata fields that appear inside error dumps
AWS_METADATA_PREFIXES = (
    "'$fault':",
    "'$metadata':",
    "httpStatusCode:",
    "requestId:",
    "extendedRequestId:",
    "cfId:",
    "attempts:",
    "totalRetryDelay:",
    "__type:",
)

# Yarn CLI noise
YARN_NOISE_PREFIXES = (
    "info Visit ",
    "warning From Yarn ",
)

# Entity array dumps: "ApplicationAnswers: [" or "migrated: ["
ENTITY_ARRAY_RE = re.compile(r"^[A-Za-z]+:?\s*\[$")


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_test_setup_noise(stripped: str) -> bool:
    # ObjectId dumps: "Application: new ObjectId(...)" or standalone "new ObjectId(...)"
    if "ObjectId(" in stripped:
        return True
    # MongoDB config lines
    if stripped.startswith(MONGO_CONFIG_PREFIXES):
        return True
    # Seed data insertion/removal logs
    if stripped.startswith(SEED_DATA_PREFIXES):
        return True
    if "was removed" in stripped and len(stripped) < 80:
        return True
    # Entity field warnings during seeding
    if "No such field in" in stripped:
        return True
    # Business data logged during setup
    if BUSINESS_DATA_RE.match(stripped):
        return True
    # Migration file array entries
    if MIGRATION_FILE_RE.match(stripped):
        return True
    # Pure numeric lines (MongoDB document IDs logged during setup)
    if stripped.isdigit():
        return True
    # Array truncation markers
    if stripped.startswith("... ") and stripped.endswith("more items"):
        return True
    # Standalone JSON brackets/commas from ObjectId/seed data blocks
    if stripped in ("{", "}", "[", "]", "],"):
        return True
    # AWS SDK error metadata (verbose per-request details, not useful for debugging)
    if stripped.startswith(AWS_METADATA_PREFIXES):
        return True
    # Yarn CLI info/warning noise
    if stripped.startswith(YARN_NOISE_PREFIXES):
        return True
    # Node.js deprecation warnings
    if stripped.startswith("(node:") or stripped.startswith(
        "(Use `node --trace-deprecation"
    ):
        return True
    # AWS SSM config fetch fallback lines (repeated per parameter, not actionable)
    if stripped.startswith("Failed to fetch ") and "from SSM" in stripped:
        return True
    # Entity array dump headers: "ApplicationAnswers: [" or "migrated: ["
    if ENTITY_ARRAY_RE.match(stripped):
        return True
    # "Error in MongoDB operation:" prefix (the actual error follows on next lines)
    if stripped == "Error in MongoDB operation:":
        return True
    return False
