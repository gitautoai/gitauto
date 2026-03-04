from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value=lambda diff_text: diff_text, raise_on_error=False
)
def ensure_diff_ab_prefixes(diff_text: str):
    lines = diff_text.split("\n")
    for i, line in enumerate(lines):
        if (
            line.startswith("--- ")
            and not line.startswith("--- a/")
            and line != "--- /dev/null"
        ):
            lines[i] = "--- a/" + line[4:]
        elif (
            line.startswith("+++ ")
            and not line.startswith("+++ b/")
            and line != "+++ /dev/null"
        ):
            lines[i] = "+++ b/" + line[4:]
    return "\n".join(lines)
