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

        # Keep line if not skipping
        if not skip:
            filtered_lines.append(line)
        elif _is_application_content(line):
            # We're skipping but this looks like application content, stop skipping
            skip = False
            filtered_lines.append(line)
        else:
            # We're skipping and this looks like pytest output, continue skipping
            content_removed = True

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def _is_application_content(line: str) -> bool:
    """Check if a line looks like application content (not pytest output)."""
    stripped = line.strip()
    if not stripped:
        return False  # Empty lines are not application content

    # Lines that start with spaces are often part of pytest output (stack traces, warnings, etc.)
    if line.startswith("  "):
        return False

    # Check if this line contains pytest-specific patterns
    pytest_patterns = [
        "platform ", "cachedir:", "rootdir:", "plugins:", "collecting", "collected",
        "test_", "PASSED", "FAILED", "SKIPPED", "ERROR", "::", ".py:",
        "DeprecationWarning", "UserWarning", "warnings.warn", "AssertionError",
        "> ", "E ", "def test_", "assert ", "[ ", "%]", " items"
    ]

    # If it contains pytest patterns, it's not application content
    if any(pattern in stripped for pattern in pytest_patterns):
        return False

    # For now, be very conservative and only consider lines that look like actual error messages
    # This is a conservative approach to avoid false positives
    return "content" in stripped.lower()
