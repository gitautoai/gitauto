from utils.error.handle_exceptions import handle_exceptions
from utils.logs.remove_ansi_escape_codes import remove_ansi_escape_codes
from utils.logs.remove_pytest_sections import remove_pytest_sections
from utils.logs.remove_repetitive_eslint_warnings import (
    remove_repetitive_eslint_warnings,
)
from utils.logs.deduplicate_logs import deduplicate_logs


@handle_exceptions(
    default_return_value=lambda error_log: error_log, raise_on_error=False
)
def clean_logs(error_log: str):
    sections_removed_log = remove_pytest_sections(error_log)
    eslint_cleaned_log = remove_repetitive_eslint_warnings(sections_removed_log)
    ansi_cleaned_log = remove_ansi_escape_codes(eslint_cleaned_log)
    minimized_log = deduplicate_logs(ansi_cleaned_log)
    return minimized_log
