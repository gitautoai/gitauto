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
            # When skipping, only stop if we encounter content that clearly looks like
            # regular log content (not pytest output) - very restrictive approach
            stripped_line = line.strip()

            if stripped_line:
                # Only stop skipping for very simple, clear content that doesn't look like pytest output
                is_simple_non_pytest_content = (
                    # Must be short (1-3 words max)
                    len(stripped_line.split()) <= 3 and
                    # Must not contain file paths, function calls, or pytest patterns
                    not any(char in stripped_line for char in [':', '(', ')', '.py', '/', '\\', '%', '[', ']']) and
                    # Must not contain pytest-related keywords
                    not any(keyword in stripped_line.lower() for keyword in [
                        'warning', 'error', 'test', 'pytest', 'deprecation', 'platform',
                        'cachedir', 'rootdir', 'plugins', 'asyncio', 'collecting', 'collected',
                        'passed', 'failed', 'skipped', 'coverage', 'lcov', 'docs', 'content'
                    ]) and
                    # Must not be indented (pytest output is often indented)
                    not stripped_line.startswith(('  ', '\t'))
                )

                if is_simple_non_pytest_content:
                    skip = False
                    filtered_lines.append(line)
                else:
                    content_removed = True
            else:
                content_removed = True

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
