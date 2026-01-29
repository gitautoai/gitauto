import os

from services.efs.get_efs_dir import get_efs_dir
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_efs_install_ready(owner: str, repo: str, name: str):
    efs_dir = get_efs_dir(owner, repo)
    bin_path = os.path.join(efs_dir, "node_modules", ".bin")

    if not os.path.exists(bin_path):
        logger.info(
            "%s: .bin dir not found at %s, created at end of install, install not complete",
            name,
            bin_path,
        )
        return False

    bin_contents = os.listdir(bin_path)
    if not bin_contents:
        logger.info(
            "%s: .bin dir exists but empty at %s, populated during linking phase, install in progress",
            name,
            bin_path,
        )
        return False

    logger.info("%s: Ready (%d binaries in .bin dir)", name, len(bin_contents))
    return True
