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

        # If we're currently skipping, check if we've encountered a new section or regular content
        if skip:
            # Check if this is a new pytest section header (but not one we want to skip)
            if "===" in line:
                # This is a section header we don't recognize, so stop skipping
                skip = False
            else:
                # Check if this line looks like regular application content (not pytest output)
                is_pytest_output = (
                    line.strip().endswith(("PASSED", "FAILED", "SKIPPED", "ERROR")) or  # Test results
                    line.strip().startswith(("test_", "::")) or  # Test names
                    "%" in line and "[" in line and "]" in line or  # Progress indicators
                    line.strip().startswith(("platform", "cachedir", "rootdir", "plugins", "collecting")) or  # Session info
                    "collected" in line and "items" in line or  # Collection info
                    line.strip().startswith(("/", "  ")) or  # File paths or indented content (common in warnings)
                    line.strip() == ""  # Empty lines within pytest sections
                )

                # If this doesn't look like pytest output, stop skipping
                if not is_pytest_output:
                    skip = False

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
