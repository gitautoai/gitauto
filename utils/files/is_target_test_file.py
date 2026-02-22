from pathlib import Path

from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.get_impl_file_from_pr_title import get_impl_file_from_pr_title
from utils.files.is_test_file import is_test_file


@handle_exceptions(default_return_value=True, raise_on_error=False)
def is_target_test_file(file_path: str, base_args: BaseArgs):
    if not is_test_file(file_path):
        # Return False (block edit) when file is not a test file
        return False

    pr_title = base_args.get("pr_title", "")
    if not pr_title:
        # Return True (allow edit) when title is missing to avoid blocking GitAuto
        return True

    implementation_file = get_impl_file_from_pr_title(pr_title)
    target_filename = Path(implementation_file).stem

    return target_filename.lower() in file_path.lower()
