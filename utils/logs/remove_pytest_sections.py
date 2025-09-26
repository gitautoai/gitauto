import re

from utils.error.handle_exceptions import handle_exceptions


def _looks_like_pytest_output(line):
    """Check if a line looks like it's part of pytest output that should be skipped."""
    line = line.strip()

    # Empty lines are part of pytest sections
    if not line:
        return True

    # Lines with === are pytest section headers
    if "===" in line:
        return True

    # Common pytest output patterns
    pytest_indicators = [
        "platform ",
        "cachedir:",
        "rootdir:",
        "plugins:",
        "collecting",
        "collected",
        " PASSED ",
        " FAILED ",
        " SKIPPED ",
        " ERROR ",
        "[ ",  # Progress indicators like [100%]
        "-- Docs:",  # Documentation links in warnings
        "::",  # Test names like test_file.py::test_name
    ]

    # Check if line contains any pytest indicators
    for indicator in pytest_indicators:
        if indicator in line:
            return True

    # Check if line looks like a test result (ends with percentage)
    if re.search(r'\[\s*\d+%\s*\]$', line):
        return True

    return False


@handle_exceptions(default_return_value="")
def remove_pytest_sections(error_log: str):
    if not error_log:
        return error_log

    lines = error_log.split("\n")
    filtered_lines = []
    skip = False
    content_removed = False

    for line in lines:
        # Start skipping at test session header
        if "===" in line and "test session starts" in line:
            skip = True
            content_removed = True
            continue

        # Start skipping at warnings summary
        if "===" in line and "warnings summary" in line:
            skip = True
            content_removed = True
            continue

        # Stop skipping and keep failures section
        if "===" in line and "FAILURES" in line:
            skip = False
            # Add blank line before FAILURES if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Stop skipping and keep short test summary
        if "===" in line and "short test summary info" in line:
            skip = False
            # Add blank line before summary if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # If we're skipping, check if this line looks like pytest output
        if skip:
            if _looks_like_pytest_output(line):
                # Skip this line as it's part of pytest output
                content_removed = True
                continue
            else:
                # This doesn't look like pytest output, stop skipping
                skip = False
                filtered_lines.append(line)
                continue

        # Keep line if not skipping
        filtered_lines.append(line)

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
