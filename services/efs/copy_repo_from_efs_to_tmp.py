import os
import shutil

from constants.efs import DEPENDENCY_DIRS
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def copy_repo_from_efs_to_tmp(efs_dir: str, clone_dir: str):
    clone_git_dir = os.path.join(clone_dir, ".git")
    if os.path.exists(clone_git_dir):
        logger.info("Reusing existing tmp clone: %s", clone_dir)
        return clone_dir

    # Only skip dependency dirs that actually exist on EFS
    dirs_to_skip = [
        d for d in DEPENDENCY_DIRS if os.path.exists(os.path.join(efs_dir, d))
    ]

    logger.info("Copying EFS to /tmp: %s -> %s", efs_dir, clone_dir)
    shutil.copytree(efs_dir, clone_dir, ignore=shutil.ignore_patterns(*dirs_to_skip))
    logger.info("Copy completed: %s", clone_dir)
    return clone_dir
