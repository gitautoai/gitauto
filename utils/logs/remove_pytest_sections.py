"""Utility functions for removing pytest sections from logs."""

import re


def remove_pytest_sections(log: str) -> str:
    """
    Remove pytest sections from log output.

    This function removes:
    1. Test session starts section (from "=== test session starts ===" to the first blank line)
    2. Test collection section (lines containing "collecting ... collected X items")
    3. Test progress lines (lines like "test_file.py::test_name PASSED [XX%]")

    Args:
        log: The pytest log output as a string

    Returns:
        The cleaned log output with specified sections removed
    """
    if not log:
        return log

    lines = log.split('\n')
    result_lines = []
    in_test_session_starts = False
    content_was_removed = False

    for line in lines:
        # Check if we're entering the test session starts section
        if "=== test session starts ===" in line:
            in_test_session_starts = True
            content_was_removed = True
            continue

        # Check if we're exiting the test session starts section (blank line or new section)
        if in_test_session_starts:
            if line.strip() == "" or "===" in line:
                in_test_session_starts = False
                if "===" in line:
                    # This line starts a new section, so we should include it
                    pass
                else:
                    # This is a blank line, skip it since we'll add our own spacing
                    continue
            else:
                # Still in test session starts section, skip this line
                continue

        # Skip collection lines
        if re.match(r'^collecting.*collected \d+ items?$', line.strip()):
            content_was_removed = True
            continue

        # Skip test progress lines
        if re.match(r'^.+::.+ (PASSED|FAILED|SKIPPED|ERROR).*\[.*\]$', line.strip()):
            content_was_removed = True
            continue

        # Handle spacing after removed content
        # We want to add a blank line before significant sections if:
        # 1. Content was removed and this line starts a new section (contains "===")
        # 2. This is "short test summary info" and the previous line isn't blank
        should_add_blank = False
        if content_was_removed and result_lines and result_lines[-1] != "":
            should_add_blank = True

        if should_add_blank:
            result_lines.append("")

        if content_was_removed:
            content_was_removed = False

        result_lines.append(line)

    return '\n'.join(result_lines)
