from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(
    default_return_value=lambda diff_text: diff_text, raise_on_error=False
)
def ensure_diff_ab_prefixes(diff_text: str):
    lines = diff_text.split("\n")
    fixed = False
    for i, line in enumerate(lines):
        if (
            line.startswith("--- ")
            and not line.startswith("--- a/")
            and line != "--- /dev/null"
        ):
            lines[i] = "--- a/" + line[4:]
            fixed = True
        elif (
            line.startswith("+++ ")
            and not line.startswith("+++ b/")
            and line != "+++ /dev/null"
        ):
            lines[i] = "+++ b/" + line[4:]
            fixed = True

    result = "\n".join(lines)
    if fixed:
        logger.info("Fixed diff a/b prefixes:\n%s\n->\n%s", diff_text, result)

    return result
