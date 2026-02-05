from pathlib import Path

from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.get_impl_file_from_issue_title import get_impl_file_from_issue_title
from utils.files.is_config_file import is_config_file
from utils.files.is_test_file import is_test_file


@handle_exceptions(default_return_value=True, raise_on_error=False)
def is_target_test_file(file_path: str, base_args: BaseArgs):
    # Config files are always allowed - they may need to be modified for test setup
    if is_config_file(file_path):
        return True

    if not is_test_file(file_path):
        # Return False (block edit) when file is not a test file
        return False

    issue_title = base_args.get("issue_title", "")
    if not issue_title:
        # Return True (allow edit) when title is missing to avoid blocking GitAuto
        return True

    implementation_file = get_impl_file_from_issue_title(issue_title)
    target_filename = Path(implementation_file).stem

    return target_filename.lower() in file_path.lower()
