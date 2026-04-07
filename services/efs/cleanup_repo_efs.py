import os
import shutil

from services.efs.get_efs_dir import get_efs_dir
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def cleanup_repo_efs(owner: str, repo: str):
    """Delete EFS directory for a repo. Called when a customer uninstalls GitAuto.
    TODO: Remove after EFS is fully removed."""
    repo_path = get_efs_dir(owner, repo)
    if not os.path.exists(repo_path):
        logger.info(
            "No EFS directory found for %s/%s, nothing to clean up", owner, repo
        )
        return True

    logger.info("Deleting EFS directory: %s", repo_path)
    shutil.rmtree(repo_path)
    logger.info("Deleted EFS directory: %s", repo_path)

    owner_path = os.path.dirname(repo_path)
    if os.path.exists(owner_path) and not os.listdir(owner_path):
        logger.info("Owner directory %s is empty, removing it", owner_path)
        os.rmdir(owner_path)
        logger.info("Successfully removed owner directory %s", owner_path)

    return True
