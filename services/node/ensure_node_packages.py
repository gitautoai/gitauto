import fcntl
import os

from config import UTF8
from services.git.git_clone_to_efs import clone_tasks
from services.node.detect_package_manager import detect_package_manager
from services.node.read_file_content import read_file_content
from services.aws.run_install_via_codebuild import run_install_via_codebuild
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


def _file_matches(efs_path: str, source_content: str | None):
    # Checks if EFS file matches source file from GitHub
    if source_content:
        if not os.path.exists(efs_path):
            return False
        with open(efs_path, "r", encoding=UTF8) as f:
            return f.read() == source_content
    return not os.path.exists(efs_path)


def _can_reuse_packages(
    efs_dir: str,
    package_json_content: str,
    npmrc_content: str | None = None,
    lock_file_name: str | None = None,
    lock_file_content: str | None = None,
):
    node_modules_path = os.path.join(efs_dir, "node_modules")
    if not os.path.exists(node_modules_path):
        return False

    # Check if .bin directory exists and has binaries (indicates complete install)
    bin_path = os.path.join(node_modules_path, ".bin")
    if not os.path.exists(bin_path):
        logger.info(
            "node: Incomplete install detected - .bin directory missing at %s", bin_path
        )
        return False

    bin_contents = os.listdir(bin_path)
    if not bin_contents:
        logger.info(
            "node: Incomplete install detected - .bin directory empty at %s", bin_path
        )
        return False

    if not _file_matches(os.path.join(efs_dir, "package.json"), package_json_content):
        return False
    if not _file_matches(os.path.join(efs_dir, ".npmrc"), npmrc_content):
        return False
    if lock_file_name and not _file_matches(
        os.path.join(efs_dir, lock_file_name), lock_file_content
    ):
        return False

    logger.info(
        "node: Reusing existing packages on EFS at %s (%d binaries in .bin)",
        efs_dir,
        len(bin_contents),
    )
    return True


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def ensure_node_packages(
    owner: str,
    owner_id: int,
    repo: str,
    branch: str,
    token: str,
    efs_dir: str,
):
    # Wait for clone to complete before installing
    clone_task = clone_tasks.get(efs_dir)
    if clone_task:
        logger.info("node: Waiting for clone task: %s", efs_dir)
        result = await clone_task
        if result:
            logger.info("node: Clone task completed: %s", efs_dir)
        else:
            logger.warning("node: Clone task failed: %s", efs_dir)

    package_json_content = read_file_content(
        "package.json",
        local_dir=efs_dir,
        owner=owner,
        repo=repo,
        branch=branch,
        token=token,
    )
    if not package_json_content:
        logger.info("node: No package.json found, skipping installation")
        return False

    npmrc_content = read_file_content(
        ".npmrc",
        local_dir=efs_dir,
        owner=owner,
        repo=repo,
        branch=branch,
        token=token,
    )

    pkg_manager, lock_file_name, lock_file_content = detect_package_manager(
        efs_dir, owner, repo, branch, token
    )

    # Ensure EFS directory exists
    os.makedirs(efs_dir, exist_ok=True)

    install_lock_path = os.path.join(efs_dir, ".install.lock")
    package_json_path = os.path.join(efs_dir, "package.json")

    if _can_reuse_packages(
        efs_dir,
        package_json_content,
        npmrc_content,
        lock_file_name,
        lock_file_content,
    ):
        return True

    with open(install_lock_path, "w", encoding=UTF8) as lock_file:
        try:
            logger.info("node: Acquiring lock for %s", efs_dir)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            logger.info("node: Lock acquired for %s", efs_dir)

            if _can_reuse_packages(
                efs_dir,
                package_json_content,
                npmrc_content,
                lock_file_name,
                lock_file_content,
            ):
                return True

            # Copy to EFS because install runs in EFS to cache node_modules across Lambda invocations
            with open(package_json_path, "w", encoding=UTF8) as f:
                f.write(package_json_content)

            if npmrc_content:
                npmrc_path = os.path.join(efs_dir, ".npmrc")
                sanitized_npmrc = npmrc_content.replace(
                    "http://registry.npmjs.org", "https://registry.npmjs.org"
                )
                with open(npmrc_path, "w", encoding=UTF8) as f:
                    f.write(sanitized_npmrc)
                logger.info("node: Wrote .npmrc to %s", npmrc_path)

            if lock_file_name and lock_file_content:
                lock_path = os.path.join(efs_dir, lock_file_name)
                with open(lock_path, "w", encoding=UTF8) as f:
                    f.write(lock_file_content)
                logger.info("node: Wrote %s to %s", lock_file_name, lock_path)

            # Trigger CodeBuild install (fire and forget, bypasses Lambda 15-min timeout)
            run_install_via_codebuild(efs_dir, owner_id, pkg_manager)
            logger.info("node: Triggered CodeBuild install for %s", efs_dir)
            return False  # Packages not ready yet, installing in background

        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            logger.info("node: Lock released for %s", efs_dir)
