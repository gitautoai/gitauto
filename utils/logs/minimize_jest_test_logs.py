from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value=lambda error_log: error_log, raise_on_error=False
)
def minimize_jest_test_logs(error_log: str) -> str:
    if not error_log:
        return error_log

    # Check if this is Jest output with the summary section
    if "Summary of all failing tests" not in error_log:
        return error_log

    lines = error_log.split("\n")
    result_lines = []
    summary_index = None

    # Keep the header (build commands at the beginning)
    in_header = True
    for i, line in enumerate(lines):
        # Keep command/header lines
        if any(
            cmd in line
            for cmd in [
                "CircleCI Build Log",
                "yarn run v",
                "npm run",
                "$ craco test",
                "$ react-scripts test",
                "$ jest",
                "$ vitest",
                "$ npm test",
                "$ yarn test",
            ]
        ):
            result_lines.append(line)
            in_header = True
        elif in_header and line.strip() == "":
            # Keep blank lines immediately after header commands
            result_lines.append(line)
        elif line.strip() == "Summary of all failing tests":
            # Found the summary section, keep everything from here onwards
            summary_index = i
            # Preserve blank lines before the summary
            if result_lines:
                # Count consecutive blank lines immediately before the summary
                blank_count = 0
                for j in range(i - 1, -1, -1):
                    if lines[j].strip() == "":
                        blank_count += 1
                    else:
                        break
                # Add the blank lines
                for _ in range(blank_count):
                    result_lines.append("")
            elif i > 0:
                # Summary is not at the beginning, add leading newline
                result_lines.append("")
            result_lines.extend(lines[i:])  # Keep everything from summary to end
            break
        else:
            # Non-blank, non-header line - we're past the header
            in_header = False

    result = "\n".join(result_lines)
    return result.rstrip()
