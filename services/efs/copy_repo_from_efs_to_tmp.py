import os
import shutil

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# node_modules.tar.gz, vendor.tar.gz: extracted separately by extract_dependencies
# index.lock: stale git lock from concurrent EFS operations
IGNORE_EFS_FILES = shutil.ignore_patterns(
    "node_modules.tar.gz", "vendor.tar.gz", "index.lock"
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def copy_repo_from_efs_to_tmp(efs_dir: str, clone_dir: str):
    clone_git_dir = os.path.join(clone_dir, ".git")
    if os.path.exists(clone_git_dir):
        logger.info("Reusing existing tmp clone: %s", clone_dir)
        return clone_dir

    logger.info("Copying EFS to /tmp: %s -> %s", efs_dir, clone_dir)

    # dirs_exist_ok=True: if clone_dir exists (e.g., read_file_content cached package.json),
    # copytree overwrites existing files with EFS versions, leaves other files untouched
    # symlinks=True: copy symlinks as symlinks instead of following them.
    # Repos may have dangling symlinks (e.g., web/api-doc) that cause ENOENT
    # when copytree tries to read the symlink target with the default symlinks=False.
    shutil.copytree(
        efs_dir,
        clone_dir,
        symlinks=True,
        ignore=IGNORE_EFS_FILES,
        dirs_exist_ok=True,
    )
    logger.info("Copy completed: %s", clone_dir)
    return clone_dir
