import re

from utils.error.handle_exceptions import handle_exceptions


def _is_pytest_section_content(line):
    """Check if a line looks like pytest section content that should be skipped."""
    # Empty lines are part of pytest sections
    if not line.strip():
        return True

    # Lines with === are pytest section headers
    if "===" in line:
        return True

    # Common pytest output patterns
    pytest_patterns = [
        "platform ",
        "cachedir:",
        "rootdir:",
        "plugins:",
        "collecting",
        "collected",
        "PASSED",
        "FAILED",
        "SKIPPED",
        "ERROR",
        "[ ",  # Progress indicators like [100%]
        "-- Docs:",  # Documentation links in warnings
    ]

    return any(pattern in line for pattern in pytest_patterns)


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

        # Keep line if not skipping
        if not skip:
            filtered_lines.append(line)
        else:
            # If we're skipping and encounter a line that doesn't look like pytest output,
            # stop skipping and include this line
            if not _is_pytest_section_content(line):
                skip = False
                filtered_lines.append(line)
            else:
                content_removed = True

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
