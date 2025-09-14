import isort
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value=lambda content, *_: content, raise_on_error=False
)
def sort_imports(content: str, file_path: str):
    if not content.strip():
        return content

    # Python files
    if file_path.endswith(".py"):
        # Use isort directly (faster than subprocess)
        return isort.code(content)

    # JavaScript/TypeScript files (future enhancement)
    if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        # Could use tools like import-sort or organize-imports-cli
        pass

    # Java files (future enhancement)
    if file_path.endswith(".java"):
        # Could use google-java-format or similar
        pass

    # Return original content if no sorting available for this file type
    return content
