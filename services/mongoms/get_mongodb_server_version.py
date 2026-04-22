import json
import re

from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger

# `@shelf/jest-mongodb` reads its settings from one of these files at the repo root.
# Order matters: the first one present wins (same order as the upstream library).
JEST_MONGODB_CONFIG_FILENAMES = (
    "jest-mongodb-config.js",
    "jest-mongodb-config.cjs",
    "jest-mongodb-config.ts",
)

# Matches e.g. `binary: { version: 'v8.0-latest', ... }` or the same with double quotes.
# Kept permissive for whitespace/newlines inside the `binary` object so it tolerates typical formatter output.
_BINARY_VERSION_RE = re.compile(
    r"binary\s*:\s*\{[^{}]*?version\s*:\s*['\"]([^'\"]+)['\"]",
    re.DOTALL,
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_mongodb_server_version(clone_dir: str):
    """Detect MongoDB version from package.json config, scripts, or jest-mongodb-config.
    Returns e.g. 'v7.0-latest' or None."""
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
        logger.info("get_mongodb_server_version: checking config.mongodbMemoryServer")
        mongoms_config = config.get("mongodbMemoryServer")
        if isinstance(mongoms_config, dict):
            logger.info(
                "get_mongodb_server_version: checking config.mongodbMemoryServer.version"
            )
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
        logger.info("get_mongodb_server_version: scanning scripts for MONGOMS_VERSION")
        for script in scripts.values():
            match = re.search(r"MONGOMS_VERSION=(\S+)", str(script))
            if match:
                logger.info(
                    "get_mongodb_server_version: found MONGOMS_VERSION=%s in scripts",
                    match.group(1),
                )
                return match.group(1)

    # Fall back to @shelf/jest-mongodb config file at the repo root.
    # Example: `mongodbMemoryServerOptions: { binary: { version: 'v8.0-latest' } }`
    logger.info(
        "get_mongodb_server_version: no MONGOMS_VERSION in scripts, checking jest-mongodb config"
    )
    for filename in JEST_MONGODB_CONFIG_FILENAMES:
        config_content = read_local_file(filename, clone_dir)
        if not config_content:
            logger.info("get_mongodb_server_version: %s not found", filename)
            continue
        match = _BINARY_VERSION_RE.search(config_content)
        if match:
            logger.info(
                "get_mongodb_server_version: found binary.version=%s in %s",
                match.group(1),
                filename,
            )
            return match.group(1)

        logger.info(
            "get_mongodb_server_version: %s present but no binary.version pattern matched",
            filename,
        )

    logger.info("get_mongodb_server_version: no MongoDB version detected")
    return None
