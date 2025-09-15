from utils.error.handle_exceptions import handle_exceptions
from utils.text.sort_imports_py import sort_python_imports
from utils.text.sort_imports_js import sort_js_ts_imports


@handle_exceptions(
    default_return_value=lambda content, *_: content, raise_on_error=False
)
def sort_imports(content: str, file_path: str):
    if not content.strip():
        return content

    # Python files
    if file_path.endswith(".py"):
        return sort_python_imports(content)

    # JavaScript/TypeScript files
    if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        return sort_js_ts_imports(content)

    # Java files (future enhancement)
    if file_path.endswith(".java"):
        # Could use google-java-format or similar
        pass

    # Return original content if no sorting available for this file type
    return content
