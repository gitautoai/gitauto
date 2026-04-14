from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger

PACKAGE_MANAGER_TO_LOCK_FILE = {
    "poetry": "poetry.lock",
    "pipenv": "Pipfile.lock",
}


@handle_exceptions(default_return_value=("pip", None, None), raise_on_error=False)
def detect_python_package_manager(local_dir: str):
    """Returns (pkg_manager, lock_file_name, lock_file_content)"""
    for pm, lock_file in PACKAGE_MANAGER_TO_LOCK_FILE.items():
        content = read_local_file(lock_file, base_dir=local_dir)
        if content:
            logger.info("python: Detected %s from %s", pm, lock_file)
            return pm, lock_file, content

    logger.info("python: No lock file found, defaulting to pip")
    return "pip", None, None
