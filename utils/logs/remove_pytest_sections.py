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

        # If we're skipping, check if this line looks like it's outside of pytest sections
        if skip and line.strip():
            # Check if this line looks like regular log content (not pytest-specific)
            is_pytest_content = (
                line.startswith(" ") or  # Indented content (stack traces, etc.)
                line.startswith("/") or  # File paths
                "::" in line or  # Test names like test_file.py::test_name
                " PASSED " in line or " FAILED " in line or " SKIPPED " in line or " ERROR " in line or  # Test results
                "platform " in line or  # Platform info
                "cachedir:" in line or "rootdir:" in line or "plugins:" in line or  # Pytest config
                "collecting" in line or "collected" in line or  # Collection info
                line.startswith("E ") or  # Error lines
                ">" in line and line.strip().startswith(">") or  # Code context lines
                "%" in line and ("[" in line and "]" in line) or  # Progress indicators like [ 50%]
                line.startswith("asyncio:") or line.startswith("plugins:")  # Additional pytest-specific lines
            )

            if not is_pytest_content:
                skip = False
                # Add blank line if we just removed content and last line isn't blank
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
