from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.logs.dedup_jest_errors import dedup_jest_errors
from utils.logs.extract_jest_summary_section import extract_jest_summary_section
from utils.logs.strip_jest_noise import strip_jest_noise
from utils.logs.strip_node_modules_from_stacktrace import (
    strip_node_modules_from_stacktrace,
)


@handle_exceptions(
    default_return_value=lambda error_log: error_log, raise_on_error=False
)
def minimize_jest_test_logs(error_log: str):
    if not error_log:
        return error_log

    # CI logs (CircleCI) have a summary section; subprocess output does not
    if "Summary of all failing tests" in error_log:
        result = extract_jest_summary_section(error_log)
    else:
        result = strip_jest_noise(error_log)

    result = strip_node_modules_from_stacktrace(result)
    result = dedup_jest_errors(result)
    logger.info("Minimized Jest log from %d to %d chars", len(error_log), len(result))
    return result.strip()
