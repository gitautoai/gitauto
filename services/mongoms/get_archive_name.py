import json
import os
import re

from constants.aws import LAMBDA_DISTRO
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_mongoms_archive_name(clone_dir: str):
    """Construct MONGOMS_ARCHIVE_NAME to bypass OS auto-detection bug in mongodb-memory-server <8. Versions <8 misdetect Amazon Linux 2023 as "amazon" (release 2023 > upper bound 3) AND lack MONGOMS_DISTRO support. 8.x has DISTRO support so MONGOMS_DISTRO covers it. 9.x+ fixed auto-detection entirely."""
    # Check installed mongodb-memory-server-core version
    mongoms_pkg_path = os.path.join(
        clone_dir, "node_modules", "mongodb-memory-server-core", "package.json"
    )
    if not os.path.isfile(mongoms_pkg_path):
        logger.info(
            "get_mongoms_archive_name: mongodb-memory-server-core not installed, skipping"
        )
        return None

    mongoms_pkg_content = read_local_file(
        os.path.join("node_modules", "mongodb-memory-server-core", "package.json"),
        clone_dir,
    )
    if not mongoms_pkg_content:
        logger.info(
            "get_mongoms_archive_name: could not read mongodb-memory-server-core package.json"
        )
        return None

    mongoms_pkg: dict[str, str] = json.loads(mongoms_pkg_content)
    mongoms_major = int(mongoms_pkg.get("version", "0").split(".")[0])
    if mongoms_major >= 8:
        logger.info(
            "get_mongoms_archive_name: mongodb-memory-server %s, DISTRO or auto-detection handles it",
            mongoms_pkg.get("version"),
        )
        return None

    # For <8, need ARCHIVE_NAME to bypass MongoDB broken OS detection. Detect MongoDB version from package.json.
    pkg_content = read_local_file("package.json", clone_dir)
    if not pkg_content:
        logger.info("get_mongoms_archive_name: no package.json found in %s", clone_dir)
        return None

    pkg: dict = json.loads(pkg_content)
    if not isinstance(pkg, dict):
        logger.info("get_mongoms_archive_name: package.json is not a dict")
        return None

    # Detect MongoDB version: config.mongodbMemoryServer.version first, then MONGOMS_VERSION in scripts
    config = pkg.get("config", {})
    mongoms_config = (
        config.get("mongodbMemoryServer", {}) if isinstance(config, dict) else {}
    )
    version = (
        mongoms_config.get("version") if isinstance(mongoms_config, dict) else None
    )

    if not version:
        logger.info(
            "get_mongoms_archive_name: no config.mongodbMemoryServer.version, checking scripts"
        )
        scripts = pkg.get("scripts", {})
        if isinstance(scripts, dict):
            for script in scripts.values():
                match = re.search(r"MONGOMS_VERSION=(\S+)", str(script))
                if match:
                    version = match.group(1)
                    logger.info(
                        "get_mongoms_archive_name: found MONGOMS_VERSION=%s in scripts",
                        version,
                    )
                    break

    if not version:
        logger.info(
            "get_mongoms_archive_name: mongodb-memory-server <8 but no MongoDB version detected, skipping"
        )
        return None

    archive_name = f"mongodb-linux-x86_64-{LAMBDA_DISTRO}-{version}.tgz"
    logger.info("get_mongoms_archive_name: %s", archive_name)
    return archive_name
