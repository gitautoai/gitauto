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
    skip_reason = None  # Track why we're skipping

    for line in lines:
        # Start skipping at test session header
        if "===" in line and "test session starts" in line:
            skip = True
            skip_reason = "test_session"
            content_removed = True
            continue

        # Start skipping at warnings summary
        if "===" in line and "warnings summary" in line:
            skip = True
            skip_reason = "warnings"
            content_removed = True
            continue

        # Stop skipping and keep failures section
        if "===" in line and "FAILURES" in line:
            skip = False
            skip_reason = None
            # Add blank line before FAILURES if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Stop skipping and keep short test summary
        if "===" in line and "short test summary info" in line:
            skip = False
            skip_reason = None
            # Add blank line before summary if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # If we encounter any other === line while skipping, stop skipping
        if skip and "===" in line:
            skip = False
            skip_reason = None
            # Add blank line before this section if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # If we're skipping due to test session, be more selective
        if skip and skip_reason == "test_session":
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                content_removed = True
                continue

            # Skip lines that contain common pytest session keywords
            pytest_session_keywords = [
                "platform",
                "cachedir",
                "rootdir",
                "plugins",
                "collecting",
                "collected",
                "PASSED",
                "FAILED",
                "SKIPPED",
                "ERROR",
            ]

            # Check if line contains pytest session keywords
            contains_pytest_keyword = any(keyword in line_stripped for keyword in pytest_session_keywords)

            # Also check for test names (contain ::) or progress indicators
            has_test_indicator = "::" in line or re.search(r'\[\s*\d+%\s*\]', line)

            if contains_pytest_keyword or has_test_indicator:
                content_removed = True
                continue
            else:
                # This line doesn't look like pytest session output, stop skipping
                skip = False
                skip_reason = None
                filtered_lines.append(line)
                continue

        # If we're skipping due to warnings, skip everything until we hit a section
        if skip and skip_reason == "warnings":
            content_removed = True
            continue

        # Keep line if not skipping
        filtered_lines.append(line)

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
