from constants.aws import LAMBDA_DISTRO
from services.mongoms.get_mongo_version import get_mongo_version
from services.node.get_dependency_major_version import get_dependency_major_version
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_mongoms_archive_name(clone_dir: str):
    """Construct MONGOMS_ARCHIVE_NAME to bypass OS auto-detection bug in mongodb-memory-server <8. Versions <8 misdetect Amazon Linux 2023 as "amazon" (release 2023 > upper bound 3) AND lack MONGOMS_DISTRO support. 8.x has DISTRO support so MONGOMS_DISTRO covers it. 9.x+ fixed auto-detection entirely."""
    mongoms_major = get_dependency_major_version(clone_dir, "mongodb-memory-server")
    if not mongoms_major:
        logger.info(
            "get_mongoms_archive_name: mongodb-memory-server not in package.json, skipping"
        )
        return None

    if mongoms_major >= 8:
        logger.info(
            "get_mongoms_archive_name: mongodb-memory-server %s.x, DISTRO or auto-detection handles it",
            mongoms_major,
        )
        return None

    # For <8, need ARCHIVE_NAME to bypass broken OS detection
    version = get_mongo_version(clone_dir)
    if not version:
        logger.info(
            "get_mongoms_archive_name: mongodb-memory-server <8 but no MongoDB version detected, skipping"
        )
        return None

    archive_name = f"mongodb-linux-x86_64-{LAMBDA_DISTRO}-{version}.tgz"
    logger.info("get_mongoms_archive_name: %s", archive_name)
    return archive_name
