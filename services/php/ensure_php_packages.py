from services.aws.s3.check_s3_dep_freshness_and_trigger_install import (
    check_s3_dep_freshness_and_trigger_install,
)
from services.aws.s3.get_dep_manifest_hash import get_dep_manifest_hash
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def ensure_php_packages(
    owner_id: int,
    clone_dir: str,
    owner_name: str,
    repo_name: str,
):
    # Read repo files from clone_dir (the PR branch cloned to /tmp)
    composer_json_content = read_local_file("composer.json", base_dir=clone_dir)
    if not composer_json_content:
        logger.info("php: No composer.json found, skipping installation")
        return False

    composer_lock_content = read_local_file("composer.lock", base_dir=clone_dir)

    manifest_hash = get_dep_manifest_hash(
        [composer_json_content, composer_lock_content]
    )

    # Build manifest files to upload to S3 for CodeBuild
    manifest_files = {"composer.json": composer_json_content}

    if composer_lock_content:
        manifest_files["composer.lock"] = composer_lock_content

    return check_s3_dep_freshness_and_trigger_install(
        owner_name=owner_name,
        repo_name=repo_name,
        owner_id=owner_id,
        pkg_manager="composer",
        tarball_name="vendor.tar.gz",  # Must match SUPPORTED_DEPENDENCY_DIRS in utils/files/is_dependency_file.py
        manifest_hash=manifest_hash,
        manifest_files=manifest_files,
        log_prefix="php",
    )
