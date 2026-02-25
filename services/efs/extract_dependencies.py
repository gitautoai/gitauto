import os
import subprocess

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Dependency directories to extract from EFS tarballs
_DEPENDENCY_DIRS = ["node_modules", "vendor"]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def extract_dependencies(efs_dir: str, clone_dir: str):
    """Extract cached dependencies from EFS tarball to clone_dir.

    EFS stores node_modules.tar.gz and vendor.tar.gz (single file, fast to read).
    Lambda extracts to local /tmp (fast, ~15-30s for 150k files).
    """
    for dep_dir in _DEPENDENCY_DIRS:
        tarball_path = os.path.join(efs_dir, f"{dep_dir}.tar.gz")
        target_path = os.path.join(clone_dir, dep_dir)

        if os.path.exists(target_path):
            logger.info(
                "Extract skip: %s already exists at %s",
                dep_dir,
                target_path,
            )
            continue

        if not os.path.exists(tarball_path):
            logger.info(
                "Extract skip: no tarball at %s",
                tarball_path,
            )
            continue

        # Extract tarball to clone_dir (-x=extract, -z=decompress gzip, -f=file, -C=target dir)
        logger.info("Extracting %s from EFS tarball...", dep_dir)
        subprocess.run(
            ["tar", "-xzf", tarball_path, "-C", clone_dir],
            check=True,
            capture_output=True,
        )
        logger.info("Extracted: %s -> %s", tarball_path, target_path)
