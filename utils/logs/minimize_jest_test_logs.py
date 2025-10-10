def return_input_on_exception(func):
    """Decorator that returns the input unchanged if an exception occurs."""

    def wrapper(input_log):
        try:
            return func(input_log)
        except Exception:
            return input_log

    return wrapper


@return_input_on_exception
def minimize_jest_test_logs(input_log):
    """Minimize Jest test logs by keeping only headers and summary section."""
    if not input_log:
        return input_log

    lines = input_log.split("\n")
    result_lines = []
    summary_found = False
    header_complete = False

    for i, line in enumerate(lines):
        # Check if we've found the summary section
        if "Summary of all failing tests" in line:
            # Add remaining lines from summary onwards
            if result_lines:
                result_lines.append("")
            result_lines.extend(lines[i:])
            summary_found = True
            break

        # Check if this line is a command/header line
        stripped_line = line.lstrip()
        is_command = False

        # Check for patterns that should be anywhere in the line
        if (
            "CircleCI Build Log" in line
            or "yarn run v" in line
            or "npm run" in line
        ):
            is_command = True
        # Check for $ commands that must start the line (after stripping)
        elif (
            stripped_line.startswith("$ craco test")
            or stripped_line.startswith("$ react-scripts test")
            or stripped_line.startswith("$ jest")
            or stripped_line.startswith("$ vitest")
            or stripped_line.startswith("$ npm test")
            or stripped_line.startswith("$ yarn test")
        ):
            is_command = True

        # Only add command lines if we're still in the header section
        if is_command and not header_complete:
            result_lines.append(line)
        elif not is_command and result_lines:
            # Once we encounter a non-command line after commands, header is complete
            header_complete = True

    return "\n".join(result_lines) if summary_found else input_log
