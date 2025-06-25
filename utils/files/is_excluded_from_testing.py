from services.supabase.coverages.types import CoverageRecord
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_excluded_from_testing(filename: str, coverage_data: dict[str, CoverageRecord]):
    if not filename or not coverage_data:
        return False

    if filename in coverage_data:
        file_info = coverage_data[filename]
        return file_info.get("is_excluded_from_testing", False) or False

    return False
