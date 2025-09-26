"""Remove pytest sections from logs while preserving important information."""

from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="")
def remove_pytest_sections(log: str) -> str:
    """Remove pytest sections from log while preserving FAILURES and short test summary."""
    if not log:
        return log

    lines = log.split("\n")
    result_lines = []
    content_was_removed = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is the start of a section to remove
        if (("test session starts" in line and "===" in line) or
            ("warnings summary" in line and "===" in line)):
            content_was_removed = True
            # Skip all lines until we find FAILURES or short test summary
            i += 1
            while i < len(lines):
                current_line = lines[i]
                if (("FAILURES" in current_line and "===" in current_line) or
                    ("short test summary info" in current_line and "===" in current_line)):
                    # We found a section to keep, break and let the main loop handle it
                    break
                i += 1
            continue

        # Check if this is a section we want to keep (FAILURES or short test summary)
        elif (("FAILURES" in line and "===" in line) or
              ("short test summary info" in line and "===" in line)):
            # Add a blank line before the section if:
            # 1. Content was removed and this is the first kept section, OR
            # 2. This is "short test summary info" and the previous line isn't blank
            should_add_blank = False
            if content_was_removed and result_lines and result_lines[-1] != "":
                should_add_blank = True
            elif "short test summary info" in line and result_lines and result_lines[-1] != "":
                should_add_blank = True

            if should_add_blank:
                result_lines.append("")

            if content_was_removed and "FAILURES" in line:
                content_was_removed = False

            result_lines.append(line)
        else:
            result_lines.append(line)

        i += 1

    return "\n".join(result_lines)
