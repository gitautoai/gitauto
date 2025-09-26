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

    # Split into lines for processing
    lines = log.split('\n')
    filtered_lines = []
    skip_mode = False

    for line in lines:
        # Check for test session starts - skip everything until FAILURES or short test summary
        if re.search(r'=+\s*test session starts\s*=+', line):
            skip_mode = True
            continue

        # Check for warnings summary - skip everything until next major section
        if re.search(r'=+\s*warnings summary\s*=+', line):
            skip_mode = True
            continue

        # Check if we should stop skipping
        if skip_mode:
            if (re.search(r'=+\s*FAILURES\s*=+', line) or
                re.search(r'=+\s*short test summary info\s*=+', line) or
                line.strip().startswith('!!!!!!!!!!!!!!!!!!!!!!!!!')):
                skip_mode = False
                # Add blank line before the section if we removed content
                if filtered_lines and filtered_lines[-1] != "":
                    filtered_lines.append("")
                # Don't skip this line, process it normally
            else:
                # Still in skip mode, skip this line
                continue

        # Skip coverage output lines
        if (line.strip().startswith("---------- coverage:") or
            line.strip().startswith("Coverage LCOV written") or
            line.strip() == "-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html"):
            continue

        # Add the line to output
        filtered_lines.append(line)

    # Clean up excessive blank lines at the end
    while filtered_lines and filtered_lines[-1] == "":
        filtered_lines.pop()

    return '\n'.join(filtered_lines)
