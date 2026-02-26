from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger

PACKAGE_MANAGER_TO_LOCK_FILE = {
    "yarn": "yarn.lock",
    "pnpm": "pnpm-lock.yaml",
    "bun": "bun.lockb",
    "npm": "package-lock.json",
}


def detect_package_manager(local_dir: str):
    # Returns lock file content for cache invalidation and reproducible installs
    for pm, lock_file in PACKAGE_MANAGER_TO_LOCK_FILE.items():
        content = read_local_file(lock_file, base_dir=local_dir)
        if content:
            logger.info("node: Detected %s from %s", pm, lock_file)
            return pm, lock_file, content

    logger.info("node: No lock file found, defaulting to npm")
    return "npm", None, None
