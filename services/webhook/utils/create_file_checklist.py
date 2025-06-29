from typing import Any

from services.webhook.utils.create_test_selection_comment import FileChecklistItem
from utils.files.is_excluded_from_testing import is_excluded_from_testing


def create_file_checklist(
    file_changes: list[dict[str, str]], coverage_data: dict[str, Any]
) -> list[FileChecklistItem]:
    checklist = []

    for file_change in file_changes:
        file_path = file_change["filename"]
        status = file_change["status"]

        is_excluded = is_excluded_from_testing(file_path, coverage_data)
        checked = not is_excluded

        coverage_info = ""
        if file_path in coverage_data:
            file_info = coverage_data[file_path]
            coverage_parts = []

            if "line_coverage" in file_info:
                coverage_parts.append(f"Line: {file_info['line_coverage']}%")
            if "function_coverage" in file_info:
                coverage_parts.append(f"Function: {file_info['function_coverage']}%")
            if "branch_coverage" in file_info:
                coverage_parts.append(f"Branch: {file_info['branch_coverage']}%")

            if coverage_parts:
                coverage_info = f" ({', '.join(coverage_parts)})"

        checklist.append(
            FileChecklistItem(
                path=file_path,
                checked=checked,
                status=status,
                coverage_info=coverage_info,
            )
        )

    return checklist
