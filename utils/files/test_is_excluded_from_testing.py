from datetime import datetime
from typing import cast
from schemas.supabase.types import Coverages
from utils.files.is_excluded_from_testing import is_excluded_from_testing


def create_coverage_record(filename: str, is_excluded: bool = False, **overrides):
    base_record = {
        "id": 1,
        "owner_id": 123,
        "repo_id": 456,
        "primary_language": "python",
        "package_name": "test_package",
        "level": "file",
        "full_path": filename,
        "statement_coverage": 80.0,
        "function_coverage": 90.0,
        "branch_coverage": 70.0,
        "path_coverage": 60.0,
        "line_coverage": 75.5,
        "uncovered_lines": "1,2,3",
        "created_at": datetime.now(),
        "created_by": "testuser",
        "updated_at": datetime.now(),
        "updated_by": "testuser",
        "github_issue_url": None,
        "uncovered_functions": "func1,func2",
        "uncovered_branches": "branch1,branch2",
        "branch_name": "main",
        "file_size": 1000,
        "is_excluded_from_testing": is_excluded,
    }
    base_record.update(overrides)
    return cast(Coverages, base_record)


def test_is_excluded_from_testing_true():
    # Arrange
    filename = "excluded_file.py"
    coverage_data = {filename: create_coverage_record(filename, is_excluded=True)}

    # Act
    result = is_excluded_from_testing(filename, coverage_data)

    # Assert
    assert result is True


def test_is_excluded_from_testing_false():
    # Arrange
    filename = "included_file.py"
    coverage_data = {filename: create_coverage_record(filename, is_excluded=False)}

    # Act
    result = is_excluded_from_testing(filename, coverage_data)

    # Assert
    assert result is False


def test_is_excluded_from_testing_missing_flag():
    # Arrange
    filename = "file_without_flag.py"
    coverage_data = {
        filename: create_coverage_record(filename, is_excluded_from_testing=None)
    }

    # Act
    result = is_excluded_from_testing(filename, coverage_data)

    # Assert
    assert result is False


def test_is_excluded_from_testing_file_not_in_coverage():
    # Arrange
    filename = "not_in_coverage.py"
    coverage_data = {
        "other_file.py": create_coverage_record("other_file.py", is_excluded=True)
    }

    # Act
    result = is_excluded_from_testing(filename, coverage_data)

    # Assert
    assert result is False


def test_is_excluded_from_testing_empty_filename():
    # Arrange
    coverage_data = {"file.py": create_coverage_record("file.py", is_excluded=True)}

    # Act
    result = is_excluded_from_testing("", coverage_data)

    # Assert
    assert result is False


def test_is_excluded_from_testing_empty_coverage_data():
    # Act
    result = is_excluded_from_testing("file.py", {})

    # Assert
    assert result is False
