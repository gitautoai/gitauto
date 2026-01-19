import os

from constants.efs import DEPENDENCY_DIRS
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def symlink_dependencies(efs_dir: str, clone_dir: str):
    for dir_name in DEPENDENCY_DIRS:
        efs_path = os.path.join(efs_dir, dir_name)
        clone_path = os.path.join(clone_dir, dir_name)

        if os.path.exists(efs_path) and not os.path.exists(clone_path):
            os.symlink(efs_path, clone_path)
            logger.info("Symlinked %s: %s -> %s", dir_name, clone_path, efs_path)
