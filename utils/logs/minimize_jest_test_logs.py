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
    header_complete = False

    for i, line in enumerate(lines):
        # Keep command/header lines
        stripped_line = line.lstrip()
        if (
            stripped_line.startswith("CircleCI Build Log")
            or stripped_line.startswith("yarn run v")
            or stripped_line.startswith("npm run")
            or stripped_line.startswith("$ craco test")
            or stripped_line.startswith("$ react-scripts test")
            or stripped_line.startswith("$ jest")
            or stripped_line.startswith("$ vitest")
            or stripped_line.startswith("$ npm test")
            or stripped_line.startswith("$ yarn test")
        ):
            result_lines.append(line)
        # Check if we've found the summary section
        elif "Summary of all failing tests" in line:
            # Add remaining lines from summary onwards
            result_lines.append("")
            result_lines.extend(lines[i:])
            return "\n".join(result_lines)
        # Mark header as complete when we encounter a non-command line
        elif result_lines and not header_complete:
            header_complete = True

    # If no summary section found, return original input
    return input_log
