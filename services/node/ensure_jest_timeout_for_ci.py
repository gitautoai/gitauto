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

CI_TIMEOUT_MS = 180000
LOCAL_TIMEOUT_MS = 5000
EXPECTED_TIMEOUT_LINE = (
    f"testTimeout: process.env.CI ? {CI_TIMEOUT_MS} : {LOCAL_TIMEOUT_MS},"
)


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

    # Find all testTimeout lines — duplicates cause last-key-wins in JS objects
    lines = content.splitlines(keepends=True)
    timeout_line_nums = [
        i for i, line in enumerate(lines) if re.match(r"\s*testTimeout\s*[:,]", line)
    ]

    # None — inject one at the top of the config object
    if len(timeout_line_nums) == 0:
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

        insert_pos = match.end()
        next_line_match = re.search(r"\n(\s+)", content[insert_pos:])
        indent = next_line_match.group(1) if next_line_match else "  "

        updated_content = (
            content[:insert_pos]
            + f"\n{indent}{EXPECTED_TIMEOUT_LINE}"
            + content[insert_pos:]
        )

    # Exactly one — check if the value is sufficient (>= 180s)
    elif len(timeout_line_nums) == 1:
        existing_line = lines[timeout_line_nums[0]]
        numbers = re.findall(r"\d+", existing_line)
        if numbers and max(int(n) for n in numbers) >= CI_TIMEOUT_MS:
            logger.info(
                "ensure_jest_timeout_for_ci: %s already has sufficient testTimeout",
                jest_config_file,
            )
            return None

        # Too low (e.g. 10000, 30000, 60000) — replace with our CI-aware value
        logger.info(
            "ensure_jest_timeout_for_ci: %s has testTimeout below %dms, updating",
            jest_config_file,
            CI_TIMEOUT_MS,
        )
        indent = re.match(r"(\s*)", existing_line)
        indent_str = indent.group(1) if indent else "  "
        lines[timeout_line_nums[0]] = f"{indent_str}{EXPECTED_TIMEOUT_LINE}\n"
        updated_content = "".join(lines)

    # Multiple — remove all but the first, then ensure the first has a sufficient value.
    # Two PRs branching from the same master can each add testTimeout, then both merge — leaving two entries where the last (often lower) value silently wins.
    else:
        logger.info(
            "ensure_jest_timeout_for_ci: %s has %d testTimeout entries, removing duplicates",
            jest_config_file,
            len(timeout_line_nums),
        )
        lines_to_remove: set[int] = set()
        for line_num in timeout_line_nums[1:]:
            lines_to_remove.add(line_num)
            if line_num > 0 and lines[line_num - 1].strip() == "":
                lines_to_remove.add(line_num - 1)
        # Also fix the first entry's value if too low
        first_line = lines[timeout_line_nums[0]]
        first_numbers = re.findall(r"\d+", first_line)
        if not first_numbers or max(int(n) for n in first_numbers) < CI_TIMEOUT_MS:
            indent = re.match(r"(\s*)", first_line)
            indent_str = indent.group(1) if indent else "  "
            lines[timeout_line_nums[0]] = f"{indent_str}{EXPECTED_TIMEOUT_LINE}\n"
        updated_content = "".join(
            line for i, line in enumerate(lines) if i not in lines_to_remove
        )
        # Fix trailing comma on the line before the removed entry if it was the last property
        updated_content = re.sub(r",(\s*\n\};)", r"\1", updated_content)

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
