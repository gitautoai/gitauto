from constants.mongoms import MONGOMS_MAJOR_TO_MONGODB_VERSION
from services.mongoms.get_distro_for_mongodb_server_version import (
    get_distro_for_mongodb_server_version,
)
from services.mongoms.get_mongodb_server_version import get_mongodb_server_version
from services.node.get_dependency_major_version import get_dependency_major_version
from services.slack.slack_notify import slack_notify
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_mongoms_archive_name(clone_dir: str):
    """Construct MONGOMS_ARCHIVE_NAME for pre-downloading MongoDB binary. Works for all mongoms versions — <8 needs it to bypass broken OS detection, >=8 benefits from pre-cached binary to avoid runtime download."""
    mongoms_major = get_dependency_major_version(clone_dir, "mongodb-memory-server")
    if not mongoms_major:
        logger.info(
            "get_mongoms_archive_name: mongodb-memory-server not in package.json, skipping"
        )
        return None

    # Try explicit version from package.json config or scripts
    mongodb_server_version = get_mongodb_server_version(clone_dir)
    if not mongodb_server_version:
        logger.info(
            "get_mongoms_archive_name: no explicit MongoDB version in package.json for mongoms %s.x, using defaults",
            mongoms_major,
        )
        mongodb_server_version = MONGOMS_MAJOR_TO_MONGODB_VERSION.get(mongoms_major)

        if not mongodb_server_version:
            min_known = min(MONGOMS_MAJOR_TO_MONGODB_VERSION)
            max_known = max(MONGOMS_MAJOR_TO_MONGODB_VERSION)
            logger.warning(
                "get_mongoms_archive_name: mongoms %s.x not in MONGOMS_MAJOR_TO_MONGODB_VERSION (range %s-%s)",
                mongoms_major,
                min_known,
                max_known,
            )

            if mongoms_major > max_known:
                mongodb_server_version = MONGOMS_MAJOR_TO_MONGODB_VERSION[max_known]
                msg = f"get_mongoms_archive_name: mongoms {mongoms_major}.x not in MONGOMS_MAJOR_TO_MONGODB_VERSION, falling back to {mongodb_server_version} (from {max_known}.x). Update constants/mongoms.py."
                logger.warning(msg)
                slack_notify(msg)

            else:
                logger.info(
                    "get_mongoms_archive_name: mongoms %s.x < %s (oldest supported), skipping",
                    mongoms_major,
                    min_known,
                )
                return None

        else:
            logger.info(
                "get_mongoms_archive_name: using default MongoDB %s for mongoms %s.x",
                mongodb_server_version,
                mongoms_major,
            )

    distro = get_distro_for_mongodb_server_version(mongodb_server_version)
    archive_name = f"mongodb-linux-x86_64-{distro}-{mongodb_server_version}.tgz"
    logger.info("get_mongoms_archive_name: %s", archive_name)
    return archive_name
