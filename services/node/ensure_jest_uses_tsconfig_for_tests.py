import re

from services.github.commits.replace_remote_file import replace_remote_file_content
from services.github.files.get_raw_content import get_raw_content
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

JEST_CONFIG_FILES = [
    "jest.config.js",
    "jest.config.ts",
    "jest.config.mjs",
    "jest.config.cjs",
]

# Pattern 1: '^.+\.tsx?$': 'ts-jest' (string, no options)
TS_JEST_STRING_PATTERN = re.compile(
    r"(['\"])\^\.\+\\\.tsx\?\$\1\s*:\s*(['\"])ts-jest\2"
)
# Pattern 2: '^.+\.tsx?$': ['ts-jest', { isolatedModules: true }] (array with options)
TS_JEST_ARRAY_PATTERN = re.compile(
    r"(['\"])\^\.\+\\\.tsx\?\$\1\s*:\s*\[\s*(['\"])ts-jest\2\s*,\s*\{([^}]*)\}\s*\]"
)


@handle_exceptions(default_return_value=(None, None), raise_on_error=False)
def ensure_jest_uses_tsconfig_for_tests(
    root_files: list[str], base_args: BaseArgs, tsconfig_path: str
):
    """
    Find and update Jest config to use the specified tsconfig file.
    Returns (path, status) where status is 'modified' or None if no update was made.
    """
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]

    jest_config_file = None
    for config_file in JEST_CONFIG_FILES:
        if config_file in root_files:
            jest_config_file = config_file
            break

    if not jest_config_file:
        logger.info("No Jest config file found in root")
        return None, None

    logger.info("Found Jest config: %s", jest_config_file)
    content = get_raw_content(
        owner=owner, repo=repo, file_path=jest_config_file, ref=new_branch, token=token
    )
    if not content:
        logger.warning("Could not fetch content for %s", jest_config_file)
        return None, None

    # Check if already using the test tsconfig
    if tsconfig_path in content:
        logger.info("Jest config already uses %s", tsconfig_path)
        return jest_config_file, None

    # Check if any tsconfig is already configured (avoid duplicate keys)
    if "tsconfig:" in content or '"tsconfig":' in content or "'tsconfig':" in content:
        logger.info("Jest config already has a tsconfig configured")
        return jest_config_file, None

    updated_content = None

    # Pattern 1: ts-jest as string -> convert to array with tsconfig
    match = TS_JEST_STRING_PATTERN.search(content)
    if match:
        original = match.group(0)
        quote = match.group(1)
        replacement = f"{quote}^.+\\\\.tsx?${quote}: [{quote}ts-jest{quote}, {{ tsconfig: {quote}{tsconfig_path}{quote} }}]"
        updated_content = content.replace(original, replacement, 1)
        logger.info("Updated ts-jest string config to array with tsconfig")

    # Pattern 2: ts-jest array -> add tsconfig to options
    if not updated_content:
        match = TS_JEST_ARRAY_PATTERN.search(content)
        if match:
            original = match.group(0)
            quote = match.group(2)
            existing_opts = match.group(3).strip()
            if existing_opts and not existing_opts.endswith(","):
                existing_opts += ", "
            new_opts = f"{existing_opts}tsconfig: {quote}{tsconfig_path}{quote}"
            key_quote = match.group(1)
            replacement = f"{key_quote}^.+\\\\.tsx?${key_quote}: [{quote}ts-jest{quote}, {{ {new_opts} }}]"
            updated_content = content.replace(original, replacement, 1)
            logger.info("Added tsconfig to existing ts-jest array config")

    if not updated_content:
        logger.info("Could not find ts-jest transform pattern to update")
        return None, None

    result = replace_remote_file_content(
        file_content=updated_content,
        file_path=jest_config_file,
        base_args=base_args,
        commit_message=f"Configure Jest to use {tsconfig_path}",
    )
    if result:
        logger.info("Modified %s to use %s", jest_config_file, tsconfig_path)
        return jest_config_file, "modified"

    return None, None
