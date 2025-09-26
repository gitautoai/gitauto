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

        # If we're skipping, check what to skip
        if skip:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                content_removed = True
                continue

            # Skip lines that are clearly pytest output
            should_skip = False

            # Check for pytest configuration and status lines
            pytest_keywords = [
                "platform", "cachedir", "rootdir", "plugins", "collecting", "collected",
                "asyncio:", "PASSED", "FAILED", "SKIPPED", "ERROR", "warning", "-- Docs:"
            ]

            if any(keyword in line_stripped for keyword in pytest_keywords):
                should_skip = True

            # Check for test progress lines (contain :: and percentage, or just percentage)
            if "::" in line and re.search(r'\[\s*\d+%\s*\]', line):
                should_skip = True

            # Check for lines that are just dots/symbols with percentage
            if re.search(r'^[.\sF]*\[\s*\d+%\s*\]$', line_stripped):
                should_skip = True

            # Check for test file paths at start of line (with or without progress indicators)
            if re.search(r'\[\s*\d+%\s*\]', line):
                should_skip = True

            if re.match(r'^(services|utils|tests?)/.*\.(py|js|ts)', line_stripped):
                should_skip = True

            # Check for warning file paths
            if "/" in line and (":" in line or ".py" in line) and ("warning" in line.lower() or line_stripped.startswith("/")):
                should_skip = True

            if should_skip:
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
