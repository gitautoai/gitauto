from constants.aws import S3_DEPENDENCY_BUCKET
from services.aws.clients import s3_client
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def cleanup_s3_deps(owner: str, repo: str):
    """Delete all S3 dependency objects for a repo. Called when a customer uninstalls GitAuto."""
    s3_prefix = f"{owner}/{repo}/"
    response = s3_client.list_objects_v2(Bucket=S3_DEPENDENCY_BUCKET, Prefix=s3_prefix)
    objects = response.get("Contents", [])
    if not objects:
        logger.info(
            "No S3 objects found under s3://%s/%s", S3_DEPENDENCY_BUCKET, s3_prefix
        )
        return True

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
    return True
