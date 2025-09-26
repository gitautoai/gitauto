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
    if log_content is None:
        return None
    if not log_content:
        return ""

    # Only process logs that contain the summary section
    if "Summary of all failing tests" not in log_content:
        return log_content

    lines = log_content.strip().split('\n')
    result_lines = []
    found_commands = False

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
            found_commands = True
        elif "Summary of all failing tests" in line:
            # Add a blank line after commands if we found any
            if found_commands and result_lines:
                result_lines.append("")

            # Found the summary section, keep everything from here onwards
            # Strip leading whitespace only from the summary line itself
            result_lines.append(line.lstrip())
            # Keep the rest of the lines as-is to preserve test failure indentation
            result_lines.extend(lines[i+1:])
            break

    return '\n'.join(result_lines)
