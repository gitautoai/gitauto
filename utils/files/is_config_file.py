import re
from utils.error.handle_exceptions import handle_exceptions

CONFIG_FILE_PATTERNS = [
    # JavaScript/TypeScript config files
    r"\.config\.",  # jest.config.ts, vite.config.js, etc.
    r"\.conf\.",  # karma.conf.js
    r"tsconfig\.",  # tsconfig.json (though .json doesn't get headers)
    r"\.eslintrc",  # .eslintrc, .eslintrc.js
    r"\.prettierrc",  # .prettierrc, .prettierrc.js
    # Python config files
    r"(^|/)conftest\.py$",  # pytest fixtures
    r"(^|/)setup\.py$",  # package setup
]


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_config_file(file_path: str):
    """Check if a file is a config file (not actual test code)."""
    if not isinstance(file_path, str):
        return False

    file_path_lower = file_path.lower()
    for pattern in CONFIG_FILE_PATTERNS:
        if re.search(pattern, file_path_lower):
            return True
    return False
