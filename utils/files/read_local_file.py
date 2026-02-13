import os

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def read_local_file(file_path: str, base_dir: str):
    """Read a file from the local filesystem."""
    full_path = os.path.join(base_dir, file_path)
    if not os.path.exists(full_path):
        logger.warning("File not found: %s", full_path)
        return None

    with open(full_path, "r", encoding=UTF8) as f:
        return f.read()
