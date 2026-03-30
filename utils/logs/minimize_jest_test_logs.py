from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.logs.dedup_jest_errors import dedup_jest_errors
from utils.logs.extract_jest_summary_section import extract_jest_summary_section
from utils.logs.strip_node_modules_from_stacktrace import (
    strip_node_modules_from_stacktrace,
)


@handle_exceptions(
    default_return_value=lambda error_log: error_log, raise_on_error=False
)
def minimize_jest_test_logs(error_log: str):
    if not error_log:
        return error_log

    if "Summary of all failing tests" not in error_log:
        logger.info("No Jest summary section found, skipping minimization")
        return error_log

    result = extract_jest_summary_section(error_log)
    result = strip_node_modules_from_stacktrace(result)
    result = dedup_jest_errors(result)
    logger.info("Minimized Jest log from %d to %d chars", len(error_log), len(result))
    return result.strip()
