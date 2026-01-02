import re
from pathlib import Path

from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file


@handle_exceptions(default_return_value=True, raise_on_error=False)
def is_target_test_file(file_path: str, base_args: BaseArgs):
    if not is_test_file(file_path):
        # Return False (block edit) when file is not a test file
        return False

    issue_title = base_args.get("issue_title", "")
    if not issue_title:
        # Return True (allow edit) when title is missing to avoid blocking GitAuto
        return True

    match = re.search(
        r"Schedule:\s+(?:Add unit tests to|Increase test coverage for)\s+(.+)",
        issue_title,
    )
    if not match:
        # Return True (allow edit) for non-schedule issues to avoid blocking GitAuto
        return True

    implementation_file = match.group(1).strip()
    target_filename = Path(implementation_file).stem

    return target_filename.lower() in file_path.lower()
