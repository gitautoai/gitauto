import isort
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda content: content)
def sort_python_imports(content: str):
    """Sort Python imports using isort."""
    if not content.strip():
        return content

    return isort.code(content)
