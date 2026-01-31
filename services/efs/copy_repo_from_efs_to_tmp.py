import os
import shutil

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def copy_repo_from_efs_to_tmp(efs_dir: str, clone_dir: str):
    clone_git_dir = os.path.join(clone_dir, ".git")
    if os.path.exists(clone_git_dir):
        logger.info("Reusing existing tmp clone: %s", clone_dir)
        return clone_dir

    logger.info("Copying EFS to /tmp: %s -> %s", efs_dir, clone_dir)

    # Skip node_modules.tar.gz (extracted separately by extract_dependencies)
    # dirs_exist_ok=True: if clone_dir exists (e.g., read_file_content cached package.json),
    # copytree overwrites existing files with EFS versions, leaves other files untouched
    shutil.copytree(
        efs_dir,
        clone_dir,
        ignore=shutil.ignore_patterns("node_modules.tar.gz"),
        dirs_exist_ok=True,
    )
    logger.info("Copy completed: %s", clone_dir)
    return clone_dir
