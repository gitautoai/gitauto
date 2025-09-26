"""Utility functions for removing pytest sections from logs."""

import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def remove_pytest_sections(log: str) -> str:
    """
    Remove pytest sections from log output.

    This function removes:
    1. Test session starts section (from "=== test session starts ===" to next section or blank line)
    2. Test progress lines (lines like "test_file.py::test_name PASSED [XX%]")
    3. Warnings summary section (from "=== warnings summary ===" to next section)

    Args:
        log: The pytest log output as a string

    Returns:
        The cleaned log output with specified sections removed
    """
    if not log:
        return log

    lines = log.split('\n')
    filtered_lines = []
    in_test_session_starts = False
    in_warnings_summary = False
    content_was_removed = False

    for line in lines:
        # Check if we're entering the test session starts section
        if "=== test session starts ===" in line:
            in_test_session_starts = True
            content_was_removed = True
            continue

        # Check if we're entering the warnings summary section
        if "=== warnings summary ===" in line:
            in_warnings_summary = True
            content_was_removed = True
            continue

        # Check if we're exiting the test session starts section
        if in_test_session_starts:
            if line.strip() == "" or "===" in line:
                in_test_session_starts = False
                if "===" in line:
                    # This line starts a new section, we'll process it below
                    pass
                else:
                    # This is a blank line, skip it since we'll add our own spacing
                    continue
            else:
                # Still in test session starts section, skip this line
                continue

        # Check if we're exiting the warnings summary section
        if in_warnings_summary:
            if "===" in line:
                in_warnings_summary = False
                # This line starts a new section, we'll process it below
            else:
                # Still in warnings summary section, skip this line
                continue

        # Skip test progress lines (like "test_file.py::test_name PASSED [XX%]")
        if re.match(r'^.+::.+ (PASSED|FAILED|SKIPPED|ERROR).*\[.*\]$', line.strip()):
            content_was_removed = True
            continue

        # Skip test file lines with progress (like "services/anthropic/test_evaluate_condition.py ....... [  0%]")
        if re.match(r'^[a-zA-Z_/]+\.py.*\[.*\]$', line.strip()):
            content_was_removed = True
            continue

        # Skip collection lines
        if re.match(r'^collecting.*collected \d+ items?$', line.strip()):
            content_was_removed = True
            continue

        # Skip standalone progress lines (like "..........                                                               [  4%]")
        if re.match(r'^[.\sF]*\s*\[\s*\d+%\]$', line.strip()):
            content_was_removed = True
            continue

        # Skip asyncio mode lines
        if line.strip().startswith('asyncio: mode='):
            content_was_removed = True
            continue

        # Skip platform/plugin lines
        if line.strip().startswith('platform ') or line.strip().startswith('rootdir: ') or line.strip().startswith('plugins: '):
            content_was_removed = True
            continue

        # Add blank line before FAILURES or short test summary if content was removed
        if content_was_removed and ("=== FAILURES ===" in line or "=== short test summary info ===" in line):
            if filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            content_was_removed = False

        filtered_lines.append(line)

    # Clean up excessive blank lines at the end
    while filtered_lines and filtered_lines[-1] == "":
        filtered_lines.pop()

    return '\n'.join(filtered_lines)
