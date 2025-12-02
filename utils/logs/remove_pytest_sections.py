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
    in_session_section = False
    in_warnings_section = False

    for line in lines:
        # Start skipping at test session header
        if "===" in line and "test session starts" in line:
            skip = True
            in_session_section = True
            content_removed = True
            continue

        # Start skipping at warnings summary
        if "===" in line and "warnings summary" in line:
            skip = True
            in_warnings_section = True
            content_removed = True
            continue

        # Stop skipping and keep failures section
        if "===" in line and "FAILURES" in line:
            skip = False
            in_session_section = False
            in_warnings_section = False
            # Add blank line before FAILURES if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Stop skipping and keep short test summary
        if "===" in line and "short test summary info" in line:
            skip = False
            in_session_section = False
            in_warnings_section = False
            # Add blank line before summary if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Detect end of session section
        if in_session_section:
            # Session section typically contains these patterns
            session_patterns = [
                line.startswith("platform "),
                line.startswith("rootdir:"),
                line.startswith("cachedir:"),
                line.startswith("plugins:"),
                line.startswith("collecting "),
                line.startswith("collected "),
                "::" in line,  # Test results
                line.strip() and all(c in ".FEsxXpP[]% " or c.isdigit() for c in line.strip()),  # Progress indicators
                "===" in line,  # Section markers
                line.strip() == "",  # Blank lines
            ]

            # If line doesn't match any session pattern, stop skipping
            if not any(session_patterns):
                skip = False
                in_session_section = False

        # Detect end of warnings section (ends with Docs line or another section)
        if in_warnings_section:
            if line.startswith("-- Docs:") or ("===" in line):
                if not ("===" in line and "warnings summary" in line):
                    # This is the end of warnings section
                    if "===" in line:
                        # This is another section, process it normally
                        in_warnings_section = False
                        skip = False
                        # Re-process this line
                        if "FAILURES" in line:
                            if content_removed and filtered_lines and filtered_lines[-1] != "":
                                filtered_lines.append("")
                            filtered_lines.append(line)
                            continue
                        elif "short test summary info" in line:
                            if content_removed and filtered_lines and filtered_lines[-1] != "":
                                filtered_lines.append("")
                            filtered_lines.append(line)
                            continue
                    else:
                        # Skip the Docs line and stop skipping after it
                        in_warnings_section = False
                        skip = False
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
