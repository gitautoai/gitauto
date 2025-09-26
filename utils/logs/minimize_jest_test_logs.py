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
    # Temporarily return input unchanged to debug the issue
    return log_content
