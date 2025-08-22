from utils.error.handle_exceptions import handle_exceptions
from utils.files.should_skip_python import should_skip_python
from utils.files.should_skip_javascript import should_skip_javascript
from utils.files.should_skip_rust import should_skip_rust
from utils.files.should_skip_java import should_skip_java
from utils.files.should_skip_go import should_skip_go
from utils.files.should_skip_cpp import should_skip_cpp
from utils.files.should_skip_ruby import should_skip_ruby
from utils.files.should_skip_php import should_skip_php
from utils.files.should_skip_csharp import should_skip_csharp


@handle_exceptions(default_return_value=False, raise_on_error=False)
def should_skip_test(filename: str, content: str = None) -> bool:
    """
    Determines if a file should be skipped for test generation.

    Returns True if the file contains only:
    - Type definitions (interfaces, TypedDict, structs, etc.)
    - Constants and literals
    - Import/export statements
    - Simple data classes without behavior

    Returns False if the file contains:
    - Functions or methods with logic
    - Class implementations with behavior
    - Any executable code beyond declarations
    """
    if not isinstance(filename, str):
        return False

    if content is None:
        return False

    if not isinstance(content, str):
        return False

    # Empty files don't need tests - skip them
    if not content.strip():
        return True

    # Get file extension
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    # Route to appropriate language analyzer
    if ext in ["js", "jsx", "ts", "tsx", "mjs", "cjs", "es6", "es", "vue", "svelte"]:
        return should_skip_javascript(content)

    if ext in ["py", "pyi", "pyx"]:
        return should_skip_python(content)

    if ext == "rs":
        return should_skip_rust(content)

    if ext in ["java", "kt", "kts", "scala"]:
        return should_skip_java(content)

    if ext in ["c", "h", "cpp", "hpp", "cc", "cxx", "hxx"]:
        return should_skip_cpp(content)

    if ext in ["rb", "rake"]:
        return should_skip_ruby(content)

    if ext in ["php", "php3", "php4", "php5", "phtml"]:
        return should_skip_php(content)

    if ext in ["cs", "vb", "fs"]:
        return should_skip_csharp(content)

    if ext == "go":
        return should_skip_go(content)

    # For other file types, default to False (conservative approach)
    return False
