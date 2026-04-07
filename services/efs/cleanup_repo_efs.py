import os
import shutil

from constants.aws import S3_DEPENDENCY_BUCKET
from services.aws.clients import s3_client
from services.efs.get_efs_dir import get_efs_dir
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def cleanup_repo_efs(owner: str, repo: str):
    """Called when a customer uninstalls GitAuto. Cleans up S3 objects and EFS directories.
    TODO: Remove EFS cleanup and rename function after EFS is removed."""

    # Clean up S3 dependency objects for this repo
    s3_prefix = f"{owner}/{repo}/"
    response = s3_client.list_objects_v2(Bucket=S3_DEPENDENCY_BUCKET, Prefix=s3_prefix)
    objects = response.get("Contents", [])
    if objects:
        for obj in objects:
            key = obj.get("Key")
            if key:
                s3_client.delete_object(Bucket=S3_DEPENDENCY_BUCKET, Key=key)
        logger.info(
            "Deleted %d S3 objects under s3://%s/%s",
            len(objects),
            S3_DEPENDENCY_BUCKET,
            s3_prefix,
        )
    else:
        logger.info(
            "No S3 objects found under s3://%s/%s", S3_DEPENDENCY_BUCKET, s3_prefix
        )

    # Clean up EFS directory (legacy, will be removed in Phase 3)
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
