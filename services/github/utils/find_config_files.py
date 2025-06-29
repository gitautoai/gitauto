from constants.dependency_files import CONFIGURATION_FILES
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def find_config_files(file_tree: list[str]) -> list[str]:
    """Search for configuration files in the file tree"""
    config_files = []

    for file_path in file_tree:
        file_name = file_path.split("/")[-1]
        for dep_file in CONFIGURATION_FILES:

            # Wildcard matching (e.g., *.csproj)
            if dep_file.startswith("*") and file_name.endswith(dep_file[1:]):
                config_files.append(file_path)

            # Exact match
            elif file_name == dep_file:
                config_files.append(file_path)

    return config_files
