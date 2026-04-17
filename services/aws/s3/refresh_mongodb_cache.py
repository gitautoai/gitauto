import os

from services.aws.run_install_via_codebuild import run_install_via_codebuild
from services.node.detect_node_version import detect_node_version
from services.node.detect_package_manager import detect_package_manager
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def refresh_mongodb_cache(
    *,
    owner_id: int,
    owner_name: str,
    repo_name: str,
    clone_dir: str,
):
    """Fire-and-forget: trigger CodeBuild to refresh mongodb-binaries on S3.
    Current run uses the cached (possibly stale) binary with MONGOMS_MD5_CHECK=false."""
    mongodb_dir = os.path.join(clone_dir, "mongodb-binaries")
    if not os.path.isdir(mongodb_dir):
        logger.info("No mongodb-binaries dir, skipping cache refresh")
        return

    pkg_manager, _, _ = detect_package_manager(clone_dir)
    node_version = detect_node_version(clone_dir)
    logger.info("Triggering CodeBuild to refresh mongodb-binaries cache")
    run_install_via_codebuild(
        s3_key_prefix=f"{owner_name}/{repo_name}",
        owner_id=owner_id,
        pkg_manager=pkg_manager,
        node_version=node_version,
    )
