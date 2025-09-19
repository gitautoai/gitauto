import re

from utils.error.handle_exceptions import handle_exceptions


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

        # If we're skipping, check if this line looks like it's outside of pytest output
        if skip and line.strip():
            # Look for lines that clearly don't belong to pytest sections
            # These are typically error messages, stack traces, or other log content
            if not _looks_like_pytest_output(line):
                skip = False
                # Add blank line if we just removed content and last line isn't blank
                if content_removed and filtered_lines and filtered_lines[-1] != "":
                    filtered_lines.append("")

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


def _looks_like_pytest_output(line: str) -> bool:
    """Check if a line looks like it belongs to pytest output."""
    # Common pytest output patterns
    pytest_patterns = [
        'platform ', 'cachedir:', 'rootdir:', 'plugins:', 'collecting', 'collected',
        'PASSED', 'FAILED', 'ERROR', 'SKIPPED', '[', '%]', '::',
        'warnings.warn', 'DeprecationWarning', 'UserWarning', 'PytestWarning',
        'test results', 'results', 'items', 'test_', '.py::', 'AssertionError', 'Traceback'
    ]

    # Check if line starts with common pytest prefixes (indented content)
    if line.startswith((' ', '\t')):
        return True

    # Check for pytest-specific patterns
    line_lower = line.lower()
    for pattern in pytest_patterns:
        if pattern.lower() in line_lower:
            return True

    # Lines that are very short or just contain common words are likely pytest output
    if len(line.strip()) < 3:
        return True

    return False
