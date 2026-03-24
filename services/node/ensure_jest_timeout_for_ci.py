import re

from constants.files import JEST_CONFIG_FILES
from services.git.write_and_commit_file import write_and_commit_file
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger

# Patterns to find the config object opening brace
CONFIG_OBJECT_PATTERNS = [
    re.compile(r"module\.exports\s*=\s*\{"),
    re.compile(r"export\s+default\s+\{"),
    re.compile(r":\s*Config(?:\.InitialOptions)?\s*=\s*\{"),
    re.compile(r"merge(?:\.recursive)?\([^{]*\{"),
]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def ensure_jest_timeout_for_ci(root_files: list[str], base_args: BaseArgs):
    clone_dir = base_args["clone_dir"]

    jest_config_file = None
    for config_file in JEST_CONFIG_FILES:
        if config_file in root_files:
            jest_config_file = config_file
            break

    if not jest_config_file:
        logger.info("ensure_jest_timeout_for_ci: No Jest config file found")
        return None

    content = read_local_file(file_path=jest_config_file, base_dir=clone_dir)
    if not content:
        logger.warning(
            "ensure_jest_timeout_for_ci: Could not read %s", jest_config_file
        )
        return None

    if "testTimeout" in content:
        logger.info(
            "ensure_jest_timeout_for_ci: %s already has testTimeout", jest_config_file
        )
        return None

    # Find the config object opening brace
    match = None
    for pattern in CONFIG_OBJECT_PATTERNS:
        match = pattern.search(content)
        if match:
            break

    if not match:
        logger.info(
            "ensure_jest_timeout_for_ci: Could not find config object pattern in %s",
            jest_config_file,
        )
        return None

    # Detect indentation from the line after the opening brace
    insert_pos = match.end()
    next_line_match = re.search(r"\n(\s+)", content[insert_pos:])
    indent = next_line_match.group(1) if next_line_match else "  "

    # Inject testTimeout as the first property: longer timeout for CI (30s) vs local (5s)
    injection = f"\n{indent}testTimeout: process.env.CI ? 180000 : 5000,"
    updated_content = content[:insert_pos] + injection + content[insert_pos:]

    result = write_and_commit_file(
        file_content=updated_content,
        file_path=jest_config_file,
        base_args=base_args,
        commit_message=f"Set testTimeout for CI stability in {jest_config_file}",
    )
    if result.success:
        logger.info(
            "ensure_jest_timeout_for_ci: Added testTimeout to %s", jest_config_file
        )
        return jest_config_file

    logger.warning("ensure_jest_timeout_for_ci: Failed to modify %s", jest_config_file)
    return None
