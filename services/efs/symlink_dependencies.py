import os

from constants.efs import DEPENDENCY_DIRS
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def symlink_dependencies(efs_dir: str, clone_dir: str):
    # Symlink cached dependencies from EFS to clone_dir so npx uses local packages
    # Example: /tmp/clone/node_modules -> /mnt/efs/owner/repo/node_modules
    for dir_name in DEPENDENCY_DIRS:
        efs_path = os.path.join(efs_dir, dir_name)
        clone_path = os.path.join(clone_dir, dir_name)

        if not os.path.exists(efs_path):
            logger.info(
                "Symlink skip: %s not in EFS yet at %s (npm install hasn't run, or no package.json in repo)",
                dir_name,
                efs_path,
            )
            continue

        if os.path.exists(clone_path):
            logger.info(
                "Symlink skip: %s already exists at %s (already symlinked from previous call, or copied during clone)",
                dir_name,
                clone_path,
            )
            continue

        os.symlink(efs_path, clone_path)
        logger.info("Symlinked: %s -> %s", clone_path, efs_path)
