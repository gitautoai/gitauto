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

        # Check if this is a coverage section line
        if "coverage:" in line or line.startswith("Coverage "):
            skip = True
            content_removed = True
            continue

        # Start skipping at warnings summary
        if "===" in line and "warnings summary" in line:
            skip = True
            in_warnings_section = True
            in_session_section = False
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

        # Handle session section content
        if in_session_section:
            # Session section typically contains these patterns
            session_patterns = [
                "platform" in line,  # Platform info
                "Python" in line and "--" in line,  # Python version
                "pytest" in line,  # Pytest version
                "pluggy" in line,  # Plugin info
                "cachedir:" in line,  # Cache directory
                "rootdir:" in line,  # Root directory
                "plugins:" in line,  # Plugins list
                "collecting" in line or "collected" in line,  # Collection info
                line.strip() == "",  # Blank lines
                ".py::" in line or "PASSED" in line or "FAILED" in line or "SKIPPED" in line,  # Test results
                "[" in line and "%" in line and "]" in line,  # Progress indicators like [100%]
                (line.strip() and not line[0].isalpha()) or line.startswith("  "),  # Indented or non-alphabetic start
            ]

            if any(session_patterns):
                # This line looks like session content, keep skipping
                skip = True
            else:
                # This line doesn't look like session content, stop skipping
                skip = False
                in_session_section = False

        # Detect end of warnings section
        if in_warnings_section:
            # Check if this is the Docs line (end of warnings)
            if line.startswith("-- Docs:"):
                # Skip this line and stop skipping after it
                in_warnings_section = False
                continue

            # Check if this is another section marker
            if "===" in line:
                # This is another section, stop warnings and process normally
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

            # Warnings section typically contains these patterns
            warnings_patterns = [
                ".py::" in line or line.strip().endswith(".py"),  # Test file references
                line.startswith("  "),  # Indented warning details
                line.strip() == "",  # Blank lines
                "Warning" in line,  # Warning messages
            ]

            # If line doesn't match any warnings pattern, stop skipping
            if not any(warnings_patterns):
                skip = False
                in_warnings_section = False

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
