import re

from utils.error.handle_exceptions import handle_exceptions


def is_pytest_section_content(line: str) -> bool:
    """Check if a line looks like pytest section content that should be removed."""
    if not line.strip():
        return True  # Empty lines within sections should be removed

    # Common pytest section content patterns
    pytest_patterns = [
        r'^platform\s+',  # platform linux -- Python 3.11.4
        r'^cachedir:',    # cachedir: .pytest_cache
        r'^rootdir:',     # rootdir: /github/workspace
        r'^plugins:',     # plugins: cov-6.0.0
        r'^collecting\s+', # collecting ... collected 2 items
        r'^collected\s+\d+\s+items?',  # collected 2 items
        r'.*::\w+\s+(PASSED|FAILED|SKIPPED)',  # test results with ::
        r'.*\.py\s+[.\sF]*\s+\[\s*\d+%\]',  # test progress lines with percentage
        r'^\s*[.\sF]+\s+\[\s*\d+%\]',  # standalone progress indicators with percentage
        r'.*\.py\s+[.\sF]*$',  # test progress lines without percentage (ending with dots/F)
        r'^/.*:\d+:.*Warning',  # warning file paths
        r'^asyncio:',  # asyncio configuration lines
        r'^\s*[.\sF]+\s*$',  # lines with only dots, spaces, and F characters (no filename)
        r'^[.\s]*\[\s*\d+%\]$',  # lines with just dots/spaces and progress
        r'^--\s+Docs:',  # documentation links
        r'^\s*warnings\.warn',  # warning code
        r'^\s*$',  # empty lines
    ]

    for pattern in pytest_patterns:
        if re.match(pattern, line):
            return True

    return False


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

        # If we're skipping, check if this line looks like pytest content
        if skip:
            if is_pytest_section_content(line):
                content_removed = True
                continue
            else:
                # This line doesn't look like pytest content, stop skipping
                skip = False
                # Add blank line before this content if we just removed content and last line isn't blank
                if content_removed and filtered_lines and filtered_lines[-1] != "":
                    filtered_lines.append("")

        # Keep line if not skipping
        filtered_lines.append(line)

    # Join and only clean up excessive blank lines if we actually removed content
    result = "\n".join(filtered_lines)
    if content_removed:
        result = re.sub(r"\n{3,}", "\n\n", result)

    return result
