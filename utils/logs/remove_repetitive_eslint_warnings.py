import re


def remove_repetitive_eslint_warnings(error_log: str | None) -> str | None:
    if not error_log:
        return error_log

    lines = error_log.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a file path line (ESLint format)
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

            # Count empty lines between last error and next content
            empty_line_count = 0
            k = j - 1
            while k > i and lines[k] == "":
                empty_line_count += 1
                k -= 1

            # Only include files that have actual errors
            if file_errors:
                result_lines.append(file_path)
                result_lines.extend(file_errors)
                # Add the empty lines that were after the file's content
                for _ in range(empty_line_count):
                    result_lines.append("")

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

    # Join result and handle trailing newline
    result = "\n".join(result_lines)

    # Preserve trailing newline behavior from input
    if error_log.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    elif not error_log.endswith("\n") and result.endswith("\n"):
        result = result.rstrip("\n")

    return result
