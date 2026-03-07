from pathlib import Path

import isort

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=lambda content, *_: content)
def sort_python_imports(content: str, file_path: str):
    """Sort Python imports using isort."""
    if not content.strip():
        logger.warning("Empty content for isort: %s", file_path)
        return content

    path = Path(file_path)
    if not path.exists():
        logger.warning("File not found for isort settings discovery: %s", file_path)
        return isort.code(content)
    return isort.code(content, file_path=path)
