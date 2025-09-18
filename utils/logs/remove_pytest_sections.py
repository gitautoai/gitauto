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

        # If we're skipping and encounter a line that clearly looks like non-pytest content,
        # stop skipping. Be very conservative here - only for truly obvious cases.
        if skip and line.strip():
            # Only stop skipping for lines that are clearly regular content
            # This is very conservative - we only stop for simple text lines
            looks_like_regular_content = (
                not line.startswith(" ") and  # Not indented
                not line.startswith("/") and  # Not a file path
                "::" not in line and "%" not in line and "=" not in line and  # No pytest markers
                "platform" not in line and "cachedir" not in line and "rootdir" not in line and
                "plugins" not in line and "collecting" not in line and "collected" not in line and
                "asyncio" not in line and " PASSED " not in line and " FAILED " not in line and
                " SKIPPED " not in line and " ERROR " not in line and not line.startswith("E ") and
                not (line.strip().startswith(".") and len(line.strip()) < 100)  # Not test progress dots
            )

            if looks_like_regular_content:
                skip = False
                if content_removed and filtered_lines and filtered_lines[-1] != "":
                    filtered_lines.append("")

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
