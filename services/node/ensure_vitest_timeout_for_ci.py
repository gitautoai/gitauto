import re

from constants.files import VITEST_CONFIG_FILES
from services.git.write_and_commit_file import write_and_commit_file
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger

# Pattern to find the test block opening brace inside defineConfig: test: {
TEST_BLOCK_PATTERN = re.compile(r"test\s*:\s*\{")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def ensure_vitest_timeout_for_ci(root_files: list[str], base_args: BaseArgs):
    clone_dir = base_args["clone_dir"]

    vitest_config_file = None
    for config_file in VITEST_CONFIG_FILES:
        if config_file in root_files:
            vitest_config_file = config_file
            break

    if not vitest_config_file:
        logger.info("ensure_vitest_timeout_for_ci: No Vitest config file found")
        return None

    content = read_local_file(file_path=vitest_config_file, base_dir=clone_dir)
    if not content:
        logger.warning(
            "ensure_vitest_timeout_for_ci: Could not read %s", vitest_config_file
        )
        return None

    if "testTimeout" in content:
        logger.info(
            "ensure_vitest_timeout_for_ci: %s already has testTimeout",
            vitest_config_file,
        )
        return None

    # Find the test: { block inside defineConfig
    match = TEST_BLOCK_PATTERN.search(content)
    if not match:
        logger.info(
            "ensure_vitest_timeout_for_ci: No test: { block found in %s",
            vitest_config_file,
        )
        return None

    # Detect indentation from the line after test: {
    insert_pos = match.end()
    next_line_match = re.search(r"\n(\s+)", content[insert_pos:])
    indent = next_line_match.group(1) if next_line_match else "      "

    # Inject testTimeout inside the test block: longer timeout for CI (3min) vs local (5s)
    injection = f"\n{indent}testTimeout: process.env.CI ? 180000 : 5000,"
    updated_content = content[:insert_pos] + injection + content[insert_pos:]

    result = write_and_commit_file(
        file_content=updated_content,
        file_path=vitest_config_file,
        base_args=base_args,
        commit_message=f"Set testTimeout for CI stability in {vitest_config_file}",
    )
    if result.success:
        logger.info(
            "ensure_vitest_timeout_for_ci: Added testTimeout to %s",
            vitest_config_file,
        )
        return vitest_config_file

    logger.warning(
        "ensure_vitest_timeout_for_ci: Failed to modify %s", vitest_config_file
    )
    return None
