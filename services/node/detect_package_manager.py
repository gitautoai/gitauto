import os

from config import UTF8
from services.github.files.get_raw_content import get_raw_content
from utils.logging.logging_config import logger

PACKAGE_MANAGER_TO_LOCK_FILE = {
    "yarn": "yarn.lock",
    "pnpm": "pnpm-lock.yaml",
    "bun": "bun.lockb",
    "npm": "package-lock.json",
}


def detect_package_manager(
    clone_dir: str | None, owner: str, repo: str, branch: str, token: str
):
    # Returns lock file content for cache invalidation and reproducible installs
    for pm, lock_file in PACKAGE_MANAGER_TO_LOCK_FILE.items():
        if clone_dir:
            lock_path = os.path.join(clone_dir, lock_file)
            if os.path.exists(lock_path):
                with open(lock_path, "r", encoding=UTF8) as f:
                    content = f.read()
                logger.info("node: Detected %s from %s", pm, lock_path)
                return pm, lock_file, content

        content = get_raw_content(
            owner=owner, repo=repo, file_path=lock_file, ref=branch, token=token
        )
        if content:
            logger.info("node: Detected %s from %s via GitHub API", pm, lock_file)
            return pm, lock_file, content

    logger.info("node: No lock file found, defaulting to npm")
    return "npm", None, None
