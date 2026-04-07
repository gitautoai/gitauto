from botocore.exceptions import ClientError

from config import UTF8
from constants.aws import S3_DEPENDENCY_BUCKET
from services.aws.clients import s3_client
from services.node.detect_node_version import DEFAULT_NODE_VERSION
from services.aws.run_install_via_codebuild import run_install_via_codebuild
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_s3_dep_freshness_and_trigger_install(
    owner_name: str,
    repo_name: str,
    owner_id: int,
    pkg_manager: str,
    tarball_name: str,  # e.g. "node_modules.tar.gz" or "vendor.tar.gz"
    manifest_hash: str,
    manifest_files: dict[str, str],  # filename -> content, uploaded to S3 for CodeBuild
    log_prefix: str,  # e.g. "node" or "php"
    node_version: str = DEFAULT_NODE_VERSION,
):
    """Check S3 tarball freshness and trigger CodeBuild if stale. Returns True if fresh."""
    # Check S3 tarball freshness via HeadObject metadata
    s3_key = f"{owner_name}/{repo_name}/{tarball_name}"
    try:
        head = s3_client.head_object(Bucket=S3_DEPENDENCY_BUCKET, Key=s3_key)
        s3_hash = head.get("Metadata", {}).get("manifest-hash")
        if s3_hash == manifest_hash:
            logger.info(
                "%s: S3 tarball is fresh (hash=%s), reusing", log_prefix, manifest_hash
            )
            return True

        logger.info(
            "%s: S3 tarball stale (s3=%s, local=%s), triggering install",
            log_prefix,
            s3_hash,
            manifest_hash,
        )

    except ClientError as e:
        error_info = e.response.get("Error")
        error_code = error_info.get("Code") if error_info else None
        if error_code in ("404", "NoSuchKey"):
            logger.info("%s: No S3 tarball found, triggering install", log_prefix)
        else:
            raise

    # Upload manifest files to S3 so CodeBuild can read them
    s3_prefix = f"{owner_name}/{repo_name}/manifests"
    for filename, content in manifest_files.items():
        s3_client.put_object(
            Bucket=S3_DEPENDENCY_BUCKET,
            Key=f"{s3_prefix}/{filename}",
            Body=content.encode(UTF8),
        )
        logger.info("%s: Uploaded %s to S3", log_prefix, filename)

    # Write manifest hash to S3 for CodeBuild to use as tarball metadata
    s3_client.put_object(
        Bucket=S3_DEPENDENCY_BUCKET,
        Key=f"{s3_prefix}/.manifest-hash",
        Body=manifest_hash.encode(UTF8),
    )
    logger.info("%s: Uploaded manifest hash to S3", log_prefix)

    # Trigger CodeBuild install (fire and forget, bypasses Lambda 15-min timeout)
    s3_key_prefix = f"{owner_name}/{repo_name}"
    run_install_via_codebuild(
        s3_key_prefix=s3_key_prefix,
        owner_id=owner_id,
        pkg_manager=pkg_manager,
        node_version=node_version,
    )
    logger.info(
        "%s: Triggered CodeBuild install for %s/%s", log_prefix, owner_name, repo_name
    )
    return False
