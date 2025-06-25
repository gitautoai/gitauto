from services.supabase.coverages.get_coverages import get_coverages
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def is_excluded_from_testing(repo_id: int, filenames: list[str]):
    if not filenames:
        return []

    # Get coverage data for the files
    coverage_data = get_coverages(repo_id=repo_id, filenames=filenames)

    # Filter out files that are excluded from testing
    included_files = []
    for filename in filenames:
        if filename in coverage_data:
            file_info = coverage_data[filename]
            # Check if the file is excluded from testing
            is_excluded = file_info.get("is_excluded_from_testing", False)
            if not is_excluded:
                included_files.append(filename)
        else:
            # If no coverage data exists, include the file by default
            included_files.append(filename)

    return included_files
