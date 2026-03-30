from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value=lambda error_log: error_log, raise_on_error=False
)
def extract_jest_summary_section(error_log: str):
    if not error_log:
        return error_log

    if "Summary of all failing tests" not in error_log:
        return error_log

    lines = error_log.split("\n")
    result_lines: list[str] = []

    # Keep the header (build commands at the beginning)
    header_complete = False
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
            result_lines.append(line)
        elif "Summary of all failing tests" in line:
            result_lines.append("")  # Add blank line before summary
            result_lines.extend(lines[i:])  # Keep everything from summary to end
            break
        elif result_lines and not header_complete:
            header_complete = True

    return "\n".join(result_lines)
