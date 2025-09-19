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

    for i, line in enumerate(lines):
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

        # If we're skipping, check if we should stop based on context
        if skip and line.strip():
            # Look ahead and behind to see if this looks like the end of a pytest section
            if _should_stop_skipping(lines, i):
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


def _should_stop_skipping(lines: list, current_index: int) -> bool:
    """Determine if we should stop skipping based on the current line and context."""
    if current_index >= len(lines):
        return True

    current_line = lines[current_index].strip()

    # If we're at the last line, stop skipping
    if current_index == len(lines) - 1:
        return True

    # Look for clear indicators that we're no longer in a pytest section
    non_pytest_indicators = [
        # Common error/log patterns that aren't pytest
        'Error:', 'Exception:', 'Traceback (most recent call last):',
        'INFO:', 'DEBUG:', 'WARNING:', 'ERROR:', 'CRITICAL:',
        # File paths that aren't test files
        'File "', 'line ', 'in ',
        # Other common log patterns
        'HTTP', 'GET', 'POST', 'PUT', 'DELETE',
    ]

    # Check if current line has clear non-pytest indicators
    for indicator in non_pytest_indicators:
        if indicator in current_line:
            return True

    # If the line doesn't contain common pytest patterns and isn't indented,
    # and it's not empty, it might be regular content
    pytest_patterns = [
        'platform', 'cachedir', 'rootdir', 'plugins', 'collecting', 'collected',
        'PASSED', 'FAILED', 'ERROR', 'SKIPPED', '[', '%]', '::',
        'warnings.warn', 'DeprecationWarning', 'UserWarning', 'PytestWarning',
        'test_', '.py', 'AssertionError', 'items', 'results'
    ]

    # If line doesn't start with whitespace and doesn't contain pytest patterns
    if (not current_line.startswith((' ', '\t')) and
        current_line and
        not any(pattern.lower() in current_line.lower() for pattern in pytest_patterns)):

        # Look at the next few lines to see if they also don't look like pytest
        look_ahead = 2
        non_pytest_count = 1  # Current line

        for j in range(1, min(look_ahead + 1, len(lines) - current_index)):
            next_line = lines[current_index + j].strip()
            if next_line and not any(pattern.lower() in next_line.lower() for pattern in pytest_patterns):
                non_pytest_count += 1

        # If multiple consecutive lines don't look like pytest, stop skipping
        if non_pytest_count >= 2:
            return True

    return False
