import re


def remove_repetitive_eslint_warnings(error_log: str):
    if not error_log:
        return error_log

    lines = error_log.split("\n")
    result_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is an ESLint file path
        if (
            line.startswith("/")
            and re.match(r".*\.(ts|js|tsx)$", line)
            and ":" not in line
        ):
            file_path = line.strip()

            # Look ahead to collect only errors (not warnings) for this file
            j = i + 1
            file_errors = []

            while j < len(lines):
                next_line = lines[j]

                # Stop if we hit another file or end marker
                if (
                    (
                        next_line.startswith("/")
                        and re.match(r".*\.(ts|js|tsx)$", next_line)
                        and ":" not in next_line
                    )
                    or next_line.startswith("✖")
                    or next_line.startswith("error Command failed")
                ):
                    break

                # Only collect error lines (not warnings)
                if re.match(r"^\s+\d+:\d+\s+error", next_line):
                    file_errors.append(next_line)

                j += 1

            # Only include files that have actual errors
            if file_errors:
                result_lines.append(file_path)
                result_lines.extend(file_errors)

            i = j  # Skip to after this file's content
        else:
            # Keep non-file lines (headers, summaries, etc.)
            # Add blank line before summary if needed
            if (
                line.startswith("✖")
                and result_lines
                and result_lines[-1] != ""
                and not result_lines[-1].startswith("/")
            ):
                result_lines.append("")
            result_lines.append(line)
            i += 1

    result = "\n".join(result_lines)
    # Match the input's trailing newline behavior
    if not error_log.endswith("\n") and result.endswith("\n"):
        result = result.rstrip("\n")
    return result
