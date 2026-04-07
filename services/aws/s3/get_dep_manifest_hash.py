import hashlib

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_dep_manifest_hash(file_contents: list[str | None]):
    """Hash manifest file contents into a single SHA256 for S3 metadata freshness check."""
    hasher = hashlib.sha256()
    for content in file_contents:
        if content:
            hasher.update(content.encode(encoding=UTF8))
    digest = hasher.hexdigest()
    logger.info("Manifest hash: %s", digest)
    return digest
