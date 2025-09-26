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

        # If we encounter any other === line while skipping, stop skipping
        if skip and "===" in line:
            skip = False
            # Add blank line before this section if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # If we're skipping, be selective about what to skip
        if skip:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                content_removed = True
                continue

            # Define patterns that indicate pytest output that should be skipped
            pytest_patterns = [
                "platform",
                "cachedir",
                "asyncio:",
                "asyncio_default_fixture_loop_scope",
                "rootdir",
                "plugins",
                "collecting",
                "collected",
                "PASSED",
                "FAILED",
                "SKIPPED",
                "ERROR",
                "warning",  # For warnings summary content
                "-- Docs:",  # Documentation links in warnings
            ]

            # Check if line contains pytest patterns
            contains_pytest_pattern = any(pattern in line_stripped.lower() for pattern in pytest_patterns)

            # Also check for test names (contain ::) or progress indicators
            has_test_indicator = "::" in line or re.search(r'\[\s*\d+%\s*\]', line)

            # Check if line looks like a file path (common in warnings)
            looks_like_path = "/" in line and (":" in line or ".py" in line)

            if contains_pytest_pattern or has_test_indicator or looks_like_path:
                content_removed = True
                continue
            else:
                # This line doesn't look like pytest output, stop skipping
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
