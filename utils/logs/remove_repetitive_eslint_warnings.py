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


            # Collect any empty lines that follow the file's content
            while j < len(lines) and lines[j] == "":
                j += 1

            # Count empty lines before next content
            empty_line_count = 0
            temp_j = j - 1
            while temp_j >= i and lines[temp_j] == "":
                empty_line_count += 1
                temp_j -= 1

            # Only include files that have actual errors
            if file_errors:
                result_lines.append(file_path)
                result_lines.extend(file_errors)
                # Add the empty lines that were after the file's content
                result_lines.extend([""] * empty_line_count)

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
    if error_log.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    elif not error_log.endswith("\n") and result.endswith("\n"):
        result = result.rstrip("\n")
    return result
