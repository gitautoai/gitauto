from pathlib import Path

import isort

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda content, *_: content)
def sort_python_imports(content: str, file_path: str):
    """Sort Python imports using isort."""
    if not content.strip():
        return content

    return isort.code(content, file_path=Path(file_path))
