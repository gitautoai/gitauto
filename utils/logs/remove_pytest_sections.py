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

        # Simple heuristic: if we're skipping and encounter a line that looks like regular content
        # (not pytest output), stop skipping
        if skip and line.strip():
            # Very simple check: if the line doesn't contain common pytest keywords
            # and doesn't start with whitespace, it's probably regular content
            pytest_keywords = ['platform', 'collected', 'items', 'PASSED', 'FAILED', 'ERROR', 'SKIPPED',
                             'warnings', 'test_', '.py', '::', '[', '%]', 'cachedir', 'rootdir', 'plugins', 'results']

            line_lower = line.lower()
            has_pytest_keyword = any(keyword.lower() in line_lower for keyword in pytest_keywords)
            is_indented = line.startswith((' ', '\t'))

            # If it doesn't have pytest keywords and isn't indented, it's probably regular content
            if not has_pytest_keyword and not is_indented:
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
