import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="")
def remove_pytest_sections(log: str) -> str:
    """Remove pytest sections from log while preserving FAILURES and short test summary."""
    if not log:
        return log

    # Use regex to remove the test session content
    # Pattern: from "test session starts" to just before "FAILURES" or "short test summary info"
    pattern = r'(={3,}.*?test session starts.*?={3,}\n)(.*?)(?=(={3,}.*?(?:FAILURES|short test summary info).*?={3,}))'

    def replacement(match):
        # Return just a newline to replace the removed content
        return "\n"

    result = re.sub(pattern, replacement, log, flags=re.DOTALL)

    # Also handle warnings summary sections that might appear after failures
    warnings_pattern = r'(={3,}.*?warnings summary.*?={3,}\n)(.*?)(?=(={3,}.*?(?:short test summary info|Docs:).*?))'
    result = re.sub(warnings_pattern, replacement, result, flags=re.DOTALL)

    return result
