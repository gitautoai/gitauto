import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="")
def remove_pytest_sections(error_log: str):
    if not error_log:
        return error_log

    lines = error_log.split("\n")
    filtered_lines = []
    skip = False
    skip_section_type = None  # Track which section we're skipping
    content_removed = False

    for line in lines:
        # Check if this is a section marker line (contains ===)
        is_marker_line = "===" in line

        # Start skipping at test session header
        if is_marker_line and "test session starts" in line:
            skip = True
            skip_section_type = "test_session"
            content_removed = True
            continue

        # Start skipping at warnings summary
        if is_marker_line and "warnings summary" in line:
            skip = True
            skip_section_type = "warnings"
            content_removed = True
            continue

        # Stop skipping and keep failures section
        if is_marker_line and "FAILURES" in line:
            skip = False
            skip_section_type = None
            # Add blank line before FAILURES if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Stop skipping and keep short test summary info
        if is_marker_line and "short test summary info" in line:
            skip = False
            skip_section_type = None
            # Add blank line before summary if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # If we're skipping and hit another marker line, continue skipping
        if skip and is_marker_line:
            content_removed = True
            continue

        # If we're skipping, check if this line belongs to the section we're skipping
        if skip:
            belongs_to_section = False

            if skip_section_type == "test_session":
                # Check if line belongs to test session section
                belongs_to_section = (
                    not line.strip() or  # blank line
                    line.startswith(" ") or  # indented
                    "::" in line or  # test path
                    line.startswith("platform ") or
                    line.startswith("cachedir:") or
                    line.startswith("rootdir:") or
                    line.startswith("plugins:") or
                    line.startswith("collected ") or
                    "PASSED" in line or
                    "FAILED" in line or
                    "SKIPPED" in line or
                    "ERROR" in line or
                    ("[" in line and "]" in line and "%" in line)  # progress like [100%]
                )
            elif skip_section_type == "warnings":
                # Check if line belongs to warnings section
                belongs_to_section = (
                    not line.strip() or  # blank line
                    line.startswith(" ") or  # indented
                    "::" in line or  # test path
                    line.startswith("--")  # docs link
                )

            if belongs_to_section:
                # Continue skipping
                content_removed = True
                continue
            else:
                # This line doesn't belong to the section, stop skipping
                skip = False
                skip_section_type = None
                filtered_lines.append(line)
                continue

        # Keep line if not skipping
        filtered_lines.append(line)

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
