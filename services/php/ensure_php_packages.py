import fcntl
import os

from config import UTF8
from services.aws.run_install_via_codebuild import run_install_via_codebuild
from utils.files.read_local_file import read_local_file
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def ensure_php_packages(
    owner_id: int,
    efs_dir: str,
):
    composer_json_content = read_local_file("composer.json", base_dir=efs_dir)
    if not composer_json_content:
        logger.info("php: No composer.json found, skipping installation")
        return False

    composer_lock_content = read_local_file("composer.lock", base_dir=efs_dir)

    os.makedirs(efs_dir, exist_ok=True)

    install_lock_path = os.path.join(efs_dir, ".install-php.lock")

    with open(install_lock_path, "w", encoding=UTF8) as lock_file:
        try:
            logger.info("php: Acquiring lock for %s", efs_dir)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            logger.info("php: Lock acquired for %s", efs_dir)

            # Check if existing packages can be reused
            vendor_path = os.path.join(efs_dir, "vendor")
            autoload_path = os.path.join(vendor_path, "autoload.php")
            composer_json_path = os.path.join(efs_dir, "composer.json")
            can_reuse = os.path.exists(vendor_path) and os.path.exists(autoload_path)

            if can_reuse:
                # Verify composer.json matches
                if os.path.exists(composer_json_path):
                    with open(composer_json_path, "r", encoding=UTF8) as f:
                        can_reuse = f.read() == composer_json_content
                else:
                    can_reuse = False

            if can_reuse and composer_lock_content:
                lock_path = os.path.join(efs_dir, "composer.lock")
                if os.path.exists(lock_path):
                    with open(lock_path, "r", encoding=UTF8) as f:
                        can_reuse = f.read() == composer_lock_content
                else:
                    can_reuse = False

            if can_reuse:
                logger.info("php: Reusing existing packages on EFS at %s", efs_dir)
                return True

            if not os.path.exists(autoload_path) and os.path.exists(vendor_path):
                logger.info(
                    "php: Incomplete install - vendor/autoload.php missing at %s",
                    autoload_path,
                )

            with open(composer_json_path, "w", encoding=UTF8) as f:
                f.write(composer_json_content)

            if composer_lock_content:
                lock_path = os.path.join(efs_dir, "composer.lock")
                with open(lock_path, "w", encoding=UTF8) as f:
                    f.write(composer_lock_content)
                logger.info("php: Wrote composer.lock to %s", lock_path)

            run_install_via_codebuild(efs_dir, owner_id, "composer")
            logger.info("php: Triggered CodeBuild install for %s", efs_dir)
            return False

        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            logger.info("php: Lock released for %s", efs_dir)
