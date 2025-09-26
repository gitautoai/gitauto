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

    for line in lines:
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

        # If we're skipping, only continue skipping for lines that clearly look like pytest output
        if skip:
            line_stripped = line.strip()

            # Always skip empty lines when in skip mode
            if not line_stripped:
                content_removed = True
                continue

            # Skip lines that clearly look like pytest output
            pytest_patterns = [
                "platform ",
                "cachedir:",
                "rootdir:",
                "plugins:",
                "collecting",
                "collected",
                " PASSED ",
                " FAILED ",
                " SKIPPED ",
                " ERROR ",
                "::",  # Test names like test_file.py::test_name
                "-- Docs:",  # Documentation links
            ]

            # Check if line matches pytest patterns
            is_pytest_line = any(pattern in line for pattern in pytest_patterns)

            # Also check for progress indicators like [100%]
            if re.search(r'\[\s*\d+%\s*\]', line):
                is_pytest_line = True

            if is_pytest_line:
                content_removed = True
                continue
            else:
                # This doesn't look like pytest output, stop skipping and include this line
                skip = False
                filtered_lines.append(line)
                continue

        # Keep line if not skipping
        filtered_lines.append(line)

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
