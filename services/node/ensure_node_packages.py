from services.aws.s3.check_s3_dep_freshness_and_trigger_install import (
    check_s3_dep_freshness_and_trigger_install,
)
from services.aws.s3.get_dep_manifest_hash import get_dep_manifest_hash
from services.node.detect_package_manager import detect_package_manager
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def ensure_node_packages(
    owner_id: int,
    clone_dir: str,
    owner_name: str,
    repo_name: str,
):
    # Read repo files from clone_dir (the PR branch cloned to /tmp)
    package_json_content = read_local_file("package.json", base_dir=clone_dir)
    if not package_json_content:
        logger.info("node: No package.json found, skipping installation")
        return False

    npmrc_content = read_local_file(".npmrc", base_dir=clone_dir)

    pkg_manager, lock_file_name, lock_file_content = detect_package_manager(clone_dir)

    manifest_hash = get_dep_manifest_hash(
        [package_json_content, lock_file_content, npmrc_content]
    )

    # Build manifest files to upload to S3 for CodeBuild
    manifest_files = {"package.json": package_json_content}

    if npmrc_content:
        sanitized_npmrc = npmrc_content.replace(
            "http://registry.npmjs.org", "https://registry.npmjs.org"
        )
        manifest_files[".npmrc"] = sanitized_npmrc

    if lock_file_name and lock_file_content:
        manifest_files[lock_file_name] = lock_file_content

    return check_s3_dep_freshness_and_trigger_install(
        owner_name=owner_name,
        repo_name=repo_name,
        owner_id=owner_id,
        pkg_manager=pkg_manager,
        tarball_name="node_modules.tar.gz",
        manifest_hash=manifest_hash,
        manifest_files=manifest_files,
        log_prefix="node",
    )
