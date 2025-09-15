import os
import subprocess
import tempfile
from config import UTF8
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda content: content)
def sort_js_ts_imports(content: str):
    """Sort JavaScript/TypeScript imports using prettier with organize-imports plugin."""
    if not content.strip():
        return content

    # Determine file extension - be more specific about TypeScript detection
    is_typescript = any(
        [
            content.endswith(".ts"),
            content.endswith(".tsx"),
            "interface " in content,
            "type " in content,
            ": string" in content,
            ": number" in content,
            "export type" in content,
            "import type" in content,
        ]
    )
    extension = ".ts" if is_typescript else ".js"

    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=extension, delete=False
    ) as temp_file:
        temp_file.write(content)
        temp_filename = temp_file.name

    # Use the ESLint config file from our codebase

    current_dir = os.path.dirname(__file__)
    config_filename = os.path.join(current_dir, "eslint.config.mjs")

    # Use ESLint - the de facto standard linter with built-in sort-imports
    subprocess.run(
        [
            "npx",
            "--yes",
            "eslint@latest",
            "--config",
            config_filename,
            "--fix",
            temp_filename,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    # Read the fixed file (ESLint modifies in place)
    with open(temp_filename, "r", encoding=UTF8) as f:
        result = f.read()

    # Clean up temp file (config file is permanent)
    try:
        os.unlink(temp_filename)
    except OSError:
        pass

    return result
