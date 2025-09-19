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
        if "=" * 3 in line and "test session starts" in line:
            skip = True
            content_removed = True
            continue

        # Start skipping at warnings summary
        if "=" * 3 in line and "warnings summary" in line:
            skip = True
            content_removed = True
            continue

        # Start skipping at coverage section (lines starting with dashes and containing coverage)
        if line.strip().startswith("-") and "coverage:" in line.lower():
            skip = True
            content_removed = True
            continue

        # Skip docs lines
        if line.strip().startswith("-- Docs:"):
            content_removed = True
            continue

        # Skip coverage LCOV lines
        if "Coverage LCOV written to file" in line:
            content_removed = True
            continue

        # Stop skipping and keep failures section
        if "=" * 3 in line and "FAILURES" in line:
            skip = False
            # Add blank line before FAILURES if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Stop skipping and keep short test summary
        if "=" * 3 in line and "short test summary info" in line:
            skip = False
            # Add blank line before summary if we just removed content and last line isn't blank
            if content_removed and filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            filtered_lines.append(line)
            continue

        # Keep line if not skipping
        if not skip:
            filtered_lines.append(line)
        else:
            # When skipping, check if we've encountered a line that looks like regular content
            # This handles cases where pytest sections don't have explicit end markers
            stripped_line = line.strip()

            if stripped_line:
                # Check if this looks like regular log content (not pytest output)
                # We look for simple phrases that don't contain pytest-specific terms
                looks_like_regular_content = (
                    # Must not contain pytest-specific keywords
                    not any(keyword in stripped_line.lower() for keyword in [
                        'platform', 'cachedir', 'rootdir', 'plugins', 'asyncio', 'collecting', 'collected',
                        'test', 'pytest', 'passed', 'failed', 'skipped', 'error', 'warning', 'coverage'
                    ]) and
                    # Must not contain test patterns
                    '::' not in stripped_line and
                    '%]' not in stripped_line and
                    # Should be a simple phrase (not too complex)
                    len(stripped_line.split()) <= 4 and
                    # Should not start with common pytest prefixes
                    not stripped_line.startswith(('  ', '\t'))
                )

                if looks_like_regular_content:
                    skip = False
                    filtered_lines.append(line)
                else:
                    content_removed = True
            else:
                # Empty lines during skipping are also removed
                content_removed = True

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
