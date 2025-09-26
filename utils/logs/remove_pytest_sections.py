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
    skip_until_section = False
    content_was_removed = False

    for line in lines:
        # Start skipping from test session starts until we hit a major section
        if "test session starts" in line and "===" in line:
            skip_until_section = True
            content_was_removed = True
            continue

        # Start skipping from warnings summary until we hit a major section
        if "warnings summary" in line and "===" in line:
            skip_until_section = True
            content_was_removed = True
            continue

        # Stop skipping when we hit FAILURES or short test summary
        if skip_until_section and ("=== FAILURES ===" in line or "=== short test summary info ===" in line):
            skip_until_section = False
            # Add blank line before the section if content was removed
            if content_was_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")

        # Skip coverage output lines
        if (line.strip().startswith("---------- coverage:") or
            line.strip().startswith("Coverage LCOV written") or
            line.strip() == "-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html"):
            content_was_removed = True
            continue

        # If we're in skip mode, continue skipping
        if skip_until_section:
            continue

        filtered_lines.append(line)

    # Clean up excessive blank lines at the end
    while filtered_lines and filtered_lines[-1] == "":
        filtered_lines.pop()

    return '\n'.join(filtered_lines)
