import json
import re

from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_mongodb_server_version(clone_dir: str):
    """Detect MongoDB version from package.json config or scripts. Returns e.g. 'v7.0-latest' or None."""
    pkg_content = read_local_file("package.json", clone_dir)
    if not pkg_content:
        logger.info(
            "get_mongodb_server_version: no package.json found in %s", clone_dir
        )
        return None

    pkg = json.loads(pkg_content)
    if not isinstance(pkg, dict):
        logger.info("get_mongodb_server_version: package.json is not a dict")
        return None

    # config.mongodbMemoryServer.version first
    config = pkg.get("config")
    if isinstance(config, dict):
        mongoms_config = config.get("mongodbMemoryServer")
        if isinstance(mongoms_config, dict):
            version = mongoms_config.get("version")
            if isinstance(version, str):
                logger.info(
                    "get_mongodb_server_version: %s from config.mongodbMemoryServer.version",
                    version,
                )
                return version

    # Fall back to MONGOMS_VERSION= in scripts
    logger.info(
        "get_mongodb_server_version: no config.mongodbMemoryServer.version, checking scripts"
    )
    scripts = pkg.get("scripts")
    if isinstance(scripts, dict):
        for script in scripts.values():
            match = re.search(r"MONGOMS_VERSION=(\S+)", str(script))
            if match:
                logger.info(
                    "get_mongodb_server_version: found MONGOMS_VERSION=%s in scripts",
                    match.group(1),
                )
                return match.group(1)

    logger.info("get_mongodb_server_version: no MongoDB version detected")
    return None
