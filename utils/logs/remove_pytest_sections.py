import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="")
def remove_pytest_sections(log: str) -> str:
    """Remove pytest sections from log while preserving FAILURES and short test summary."""
    if not log:
        return log

    lines = log.split("\n")
    result_lines = []
    blank_line_added = False
    content_was_removed = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is the start of a test session or warnings summary
        if (("test session starts" in line and "===" in line) or
            ("warnings summary" in line and "===" in line)):
            content_was_removed = True
            # Skip all lines until we find FAILURES or short test summary
            i += 1
            while i < len(lines):
                current_line = lines[i]
                if (("FAILURES" in current_line and "===" in current_line) or
                    ("short test summary info" in current_line and "===" in current_line)):
                    # Add a blank line before the section if the last line isn't blank
                    if result_lines and result_lines[-1] != "":
                        result_lines.append("")
                    result_lines.append(current_line)
                    i += 1
                    break
                i += 1
            continue
        else:
            result_lines.append(line)

        i += 1

    return "\n".join(result_lines)
