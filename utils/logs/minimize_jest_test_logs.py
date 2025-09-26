from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value=lambda error_log: error_log, raise_on_error=False
)
def minimize_jest_test_logs(log_content):
    """
    Minimize Jest test logs by keeping only command lines and test failure summaries.

    Args:
        log_content (str): The full log content

    Returns:
        str: Minimized log content with only essential information
    """
    if not log_content:
        return ""

    # Only process logs that contain the summary section
    if "Summary of all failing tests" not in log_content:
        return log_content

    lines = log_content.strip().split('\n')
    result_lines = []
    last_was_command = False
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
            result_lines.append(line.lstrip())
            last_was_command = True
        elif line.strip() == "" and last_was_command and not header_complete:
            # Keep blank lines immediately after command lines
            result_lines.append("")
            last_was_command = False
        elif "Summary of all failing tests" in line:
            # Found the summary section, keep everything from here onwards
            # Strip leading whitespace only from the summary line itself
            result_lines.append(line.lstrip())
            # Keep the rest of the lines as-is to preserve test failure indentation
            result_lines.extend(lines[i+1:])
            break
        elif last_was_command and line.strip() != "":
            # Non-empty line after command means header section is complete
            header_complete = True
            last_was_command = False
        else:
            # Skip all other lines until we reach the summary
            last_was_command = False
            if not header_complete and line.strip() != "":
                header_complete = True

    return '\n'.join(result_lines)
