import fcntl
import os

from config import UTF8
from services.aws.run_install_via_codebuild import run_install_via_codebuild
from services.git.git_clone_to_efs import clone_tasks
from services.node.detect_package_manager import detect_package_manager
from services.node.read_file_content import read_file_content
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


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

    with open(install_lock_path, "w", encoding=UTF8) as lock_file:
        try:
            logger.info("node: Acquiring lock for %s", efs_dir)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            logger.info("node: Lock acquired for %s", efs_dir)

            # Check if existing packages can be reused
            node_modules_path = os.path.join(efs_dir, "node_modules")
            bin_path = os.path.join(node_modules_path, ".bin")
            package_json_path = os.path.join(efs_dir, "package.json")
            can_reuse = os.path.exists(node_modules_path)

            if can_reuse:
                if not os.path.exists(bin_path):
                    logger.info(
                        "node: Incomplete install - .bin directory missing at %s",
                        bin_path,
                    )
                    can_reuse = False
                else:
                    bin_contents = os.listdir(bin_path)
                    if not bin_contents:
                        logger.info(
                            "node: Incomplete install - .bin directory empty at %s",
                            bin_path,
                        )
                        can_reuse = False

            if can_reuse:
                # Verify package.json matches
                if os.path.exists(package_json_path):
                    with open(package_json_path, "r", encoding=UTF8) as f:
                        can_reuse = f.read() == package_json_content
                else:
                    can_reuse = False

            if can_reuse and npmrc_content:
                npmrc_path = os.path.join(efs_dir, ".npmrc")
                if os.path.exists(npmrc_path):
                    with open(npmrc_path, "r", encoding=UTF8) as f:
                        can_reuse = f.read() == npmrc_content
                else:
                    can_reuse = False

            if can_reuse and npmrc_content is None:
                # No .npmrc in repo, but if one exists on EFS, it's stale
                npmrc_path = os.path.join(efs_dir, ".npmrc")
                if os.path.exists(npmrc_path):
                    can_reuse = False

            if can_reuse and lock_file_name:
                lock_path = os.path.join(efs_dir, lock_file_name)
                if lock_file_content:
                    if os.path.exists(lock_path):
                        with open(lock_path, "r", encoding=UTF8) as f:
                            can_reuse = f.read() == lock_file_content
                    else:
                        can_reuse = False

            if can_reuse:
                logger.info(
                    "node: Reusing existing packages on EFS at %s (%d binaries in .bin)",
                    efs_dir,
                    len(os.listdir(bin_path)),
                )
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
