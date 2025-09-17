import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda error_log: error_log)
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

        # Start skipping at coverage section
        if "coverage:" in line and "----------" in line:
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

        # If we're currently skipping and encounter any other section header, stop skipping
        if skip and "===" in line:
            # This is a section header we don't recognize as pytest-specific, so stop skipping
            skip = False
            filtered_lines.append(line)
            continue

        # If we're skipping and encounter a line that doesn't look like pytest output, stop skipping
        if skip and "===" not in line and not _is_pytest_line(line):
            skip = False
            # Add this line since it's not pytest output
            filtered_lines.append(line)
            continue

        # Keep line if not skipping
        if not skip:
            filtered_lines.append(line)
        else:
            content_removed = True

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def _is_pytest_line(line: str) -> bool:
    """Check if a line looks like pytest output."""
    stripped = line.strip()
    if not stripped:
        return True  # Empty lines are part of pytest output

    # Common pytest output patterns - be more specific to avoid false positives
    pytest_patterns = [
        "platform ", "cachedir:", "rootdir:", "plugins:", "collecting",
        "test_", "PASSED", "FAILED", "SKIPPED", "ERROR", "::", "[ ", "%]",
        "collected ", " items", "warnings.warn", "DeprecationWarning",
        "UserWarning", ".py:", "AssertionError", "def test_",
        "> ", "E ", "assert "
    ]

    return any(pattern in stripped for pattern in pytest_patterns)
