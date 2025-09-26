import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="")
def remove_pytest_sections(log: str) -> str:
    """Remove pytest sections from log while preserving FAILURES and short test summary."""
    if not log:
        return log

    # Split into lines
    lines = log.split("\n")
    result_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is the start of a test session
        if "test session starts" in line and "===" in line:
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
                    i += 1  # Move to next line after adding this one
                    break
                i += 1
            # Don't increment i again since we already did it in the inner loop
            continue
        else:
            result_lines.append(line)

        i += 1

    return "\n".join(result_lines)
