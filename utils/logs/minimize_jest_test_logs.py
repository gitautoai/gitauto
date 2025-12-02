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

    # Find the index of the summary line
    summary_index = None
    for i, line in enumerate(lines):
        if line.strip() == "Summary of all failing tests":
            summary_index = i
            break

    if summary_index is None:
        return error_log

    # Keep header lines (commands at the beginning)
    header_end_index = 0
    for i, line in enumerate(lines):
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
            header_end_index = i + 1
        elif header_end_index > 0 and i < summary_index and line.strip() == "" and i == header_end_index:
            # Keep only one blank line immediately after header commands
            header_end_index = i + 1
            break
        elif header_end_index > 0:
            # We've hit a non-blank, non-header line, so we're done with the header
            break

    # Build the result
    result_lines = []

    # Add header lines
    for i in range(header_end_index):
        result_lines.append(lines[i])

    # Add a blank line between header and summary
    # - If there's a header and it doesn't end with a blank line, add one
    # - If there's no header but there's content before the summary, add one
    if (header_end_index > 0 and lines[header_end_index - 1].strip() != "") or \
       (header_end_index == 0 and summary_index > 0):
        result_lines.append("")

    # Add summary and everything after
    result_lines.extend(lines[summary_index:])

    result = "\n".join(result_lines)
    return result.rstrip()
