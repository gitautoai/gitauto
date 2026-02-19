import os

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def write_local_file(file_path: str, base_dir: str, content: str):
    """Write content to a file in the local filesystem."""
    full_path = os.path.join(base_dir, file_path)

    # Ensure full_path exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w", encoding=UTF8, newline="\n") as f:
        f.write(content)
    logger.info("Wrote local file: %s", full_path)
    return True
