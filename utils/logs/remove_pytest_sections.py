"""Utility functions for removing pytest sections from logs."""

import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def remove_pytest_sections(log: str) -> str:
    """
    Remove pytest sections from log output.

    This function removes:
    1. Test session starts section and all test progress output
    2. Warnings summary section
    3. Coverage output lines

    Args:
        log: The pytest log output as a string

    Returns:
        The cleaned log output with specified sections removed
    """
    if not log:
        return log

    lines = log.split('\n')
    filtered_lines = []
    skip_mode = False
    content_was_removed = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for test session starts - skip everything until FAILURES or short test summary
        if "test session starts" in line and "===" in line:
            skip_mode = True
            content_was_removed = True
            i += 1
            continue

        # Check for warnings summary - skip everything until next major section
        if "warnings summary" in line and "===" in line:
            skip_mode = True
            content_was_removed = True
            i += 1
            continue

        # Check if we should stop skipping
        if skip_mode:
            if ("=== FAILURES ===" in line or
                "=== short test summary info ===" in line or
                "!!!!!!!!!!!!!!!!!!!!!!!!!" in line):
                skip_mode = False
                # Add blank line before the section if content was removed
                if content_was_removed and filtered_lines and filtered_lines[-1] != "":
                    filtered_lines.append("")
                # Don't skip this line, process it normally
            else:
                # Still in skip mode, skip this line
                i += 1
                continue

        # Skip coverage output lines
        if (line.strip().startswith("---------- coverage:") or
            line.strip().startswith("Coverage LCOV written") or
            line.strip() == "-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html"):
            content_was_removed = True
            i += 1
            continue

        # Add the line to output
        filtered_lines.append(line)
        i += 1

    # Clean up excessive blank lines at the end
    while filtered_lines and filtered_lines[-1] == "":
        filtered_lines.pop()

    return '\n'.join(filtered_lines)
