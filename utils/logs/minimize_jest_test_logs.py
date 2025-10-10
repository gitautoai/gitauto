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

    for i, line in enumerate(lines):
        if "Summary of all failing tests" in line:
            # Add empty line before summary if needed
            if result_lines and result_lines[-1].strip():
                result_lines.append("")
            # Add remaining lines from summary onwards
            result_lines.extend(lines[i:])
            summary_found = True
            break

        # Skip empty lines in the header section
        if not line.strip():
            continue

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

        if is_command:
            result_lines.append(line)

    return "\n".join(result_lines) if summary_found else input_log
