from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_code_file import is_code_file
from utils.files.is_config_file import is_config_file
from utils.files.is_migration_file import is_migration_file
from utils.files.is_test_file import is_test_file
from utils.files.is_type_file import is_type_file


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_source_file(file_path: str):
    return (
        is_code_file(file_path)
        and not is_test_file(file_path)
        and not is_config_file(file_path)
        and not is_migration_file(file_path)
        and not is_type_file(file_path)
    )
