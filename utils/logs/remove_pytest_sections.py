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
    in_pytest_output = False

    for line in lines:
        # Check if this is a section marker line (contains ===)
        is_marker_line = "===" in line

        # Start skipping at test session header
        if is_marker_line and "test session starts" in line:
            skip = True
            in_pytest_output = True
            content_removed = True
            continue

        # Start skipping at warnings summary
        if is_marker_line and "warnings summary" in line:
            skip = True
            in_pytest_output = True
            content_removed = True
            continue

        # Stop skipping and keep failures section
        if is_marker_line and "FAILURES" in line:
            skip = False
            in_pytest_output = True
            # Add blank line before FAILURES if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Stop skipping and keep short test summary info
        if is_marker_line and "short test summary info" in line:
            skip = False
            in_pytest_output = True
            # Add blank line before summary if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # If we're skipping and hit another marker line, check what it is
        if skip and is_marker_line:
            # If it's a final summary line (e.g., "=== 1 passed in 0.01s ==="), stop skipping
            # These lines typically contain "passed", "failed", "in", "warnings"
            if any(keyword in line for keyword in [" passed", " failed", " skipped", " error", " in "]):
                skip = False
                in_pytest_output = False
                content_removed = True
                continue
            # Otherwise, it's another section marker, continue skipping
            content_removed = True
            continue

        # If we're skipping, continue skipping
        if skip:
            content_removed = True
            continue

        # If we're not skipping, add the line
        filtered_lines.append(line)

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
