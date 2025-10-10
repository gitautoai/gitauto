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

    # Keep the header (build commands at the beginning)
    header_complete = False
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
        elif "Summary of all failing tests" in line:
            # Found the summary section, keep everything from here onwards
            if result_lines:  # Only add blank line if there's a header
                result_lines.append("")  # Add blank line before summary
            result_lines.extend(lines[i:])  # Keep everything from summary to end
            break
        elif result_lines and not header_complete:
            # After we have header lines, we're done with the header
            header_complete = True

    result = "\n".join(result_lines)
    return result.strip()
