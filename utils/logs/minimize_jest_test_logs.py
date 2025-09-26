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

    lines = log_content.strip().split('\n')
    result_lines = []
    last_was_command = False

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
        elif "Summary of all failing tests" in line:
            # Found the summary section, keep everything from here onwards
            # Strip leading whitespace only from the summary line itself
            result_lines.append(line.lstrip())
            # Keep the rest of the lines as-is to preserve test failure indentation
            result_lines.extend(lines[i+1:])
            break
        elif line.strip() == "" and last_was_command:
            result_lines.append("")
            last_was_command = False
        else:
            last_was_command = False

    return '\n'.join(result_lines)
