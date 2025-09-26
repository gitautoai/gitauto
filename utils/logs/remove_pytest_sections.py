import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="")
def remove_pytest_sections(log: str) -> str:
    """Remove pytest sections from log while preserving FAILURES and short test summary."""
    if not log:
        return log

    # Remove test session content: from "test session starts" line to just before "FAILURES"
    # This pattern captures everything from the test session start line through all test progress
    # until it reaches a line with "FAILURES" or "short test summary info"

    # First, handle the main test session
    pattern = r'={3,}.*?test session starts.*?={3,}\n.*?(?=={3,}.*?(?:FAILURES|short test summary info).*?={3,})'
    result = re.sub(pattern, '\n', log, flags=re.DOTALL)

    # Also remove warnings summary sections if they appear before failures
    warnings_pattern = r'={3,}.*?warnings summary.*?={3,}\n.*?(?=={3,}.*?(?:FAILURES|short test summary info).*?={3,})'
    result = re.sub(warnings_pattern, '\n', result, flags=re.DOTALL)

    return result
