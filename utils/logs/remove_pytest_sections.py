import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="")
def remove_pytest_sections(log: str) -> str:
    """Remove pytest sections from log while preserving FAILURES and short test summary."""
    if not log:
        return log

    lines = log.split("\n")
    filtered_lines = []
    in_test_session = False
    content_was_removed = False

    for line in lines:
        # Start of test session - start removing content
        if "test session starts" in line and "===" in line:
            in_test_session = True
            continue

        # Start of warnings summary - start removing content
        if "warnings summary" in line and "===" in line:
            in_test_session = True
            continue

        # End of removable sections - stop removing content
        if (("FAILURES" in line and "===" in line) or
            ("short test summary info" in line and "===" in line)):
            in_test_session = False
            # Add blank line before this section if we removed content and last line isn't blank
            if content_was_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # If we're in a test session, remove the content
        if in_test_session:
            content_was_removed = True
            continue

        # Keep all other lines
        filtered_lines.append(line)

    # Join the lines back together
    result = "\n".join(filtered_lines)

    # Clean up excessive blank lines if we removed content
    if content_was_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
