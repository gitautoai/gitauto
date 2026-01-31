import os
import subprocess

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def extract_dependencies(efs_dir: str, clone_dir: str):
    # Extract cached dependencies from EFS tarball to clone_dir
    # EFS stores node_modules.tar.gz (single file, fast to read)
    # Lambda extracts to local /tmp (fast, ~15-30s for 150k files)
    tarball_path = os.path.join(efs_dir, "node_modules.tar.gz")
    target_path = os.path.join(clone_dir, "node_modules")

    if os.path.exists(target_path):
        logger.info(
            "Extract skip: node_modules already exists at %s",
            target_path,
        )
        return

    if not os.path.exists(tarball_path):
        logger.info(
            "Extract skip: no tarball at %s (not a Node.js project or CodeBuild hasn't run)",
            tarball_path,
        )
        return

    # Extract tarball to clone_dir (-x=extract, -z=decompress gzip, -f=file, -C=target dir)
    subprocess.run(
        ["tar", "-xzf", tarball_path, "-C", clone_dir],
        check=True,
        capture_output=True,
    )
    logger.info("Extracted: %s -> %s", tarball_path, target_path)
