from unittest.mock import patch
from utils.files.is_excluded_from_testing import is_excluded_from_testing


@patch("utils.files.is_excluded_from_testing.get_coverages")
def test_is_excluded_from_testing_true(mock_get_coverages):
    # Arrange
    repo_id = 123
    filename = "excluded_file.py"
    mock_get_coverages.return_value = {filename: {"is_excluded_from_testing": True}}

    # Act
    result = is_excluded_from_testing(repo_id=repo_id, filenames=[filename])

    # Assert
    assert result is True
    mock_get_coverages.assert_called_once_with(repo_id=repo_id, filenames=[filename])


@patch("utils.files.is_excluded_from_testing.get_coverages")
def test_is_excluded_from_testing_false(mock_get_coverages):
    # Arrange
    repo_id = 123
    filename = "included_file.py"
    mock_get_coverages.return_value = {filename: {"is_excluded_from_testing": False}}

    # Act
    result = is_excluded_from_testing(repo_id=repo_id, filenames=[filename])

    # Assert
    assert result is False


@patch("utils.files.is_excluded_from_testing.get_coverages")
def test_is_excluded_from_testing_no_coverage_data(mock_get_coverages):
    # Arrange
    repo_id = 123
    filename = "no_coverage_file.py"
    mock_get_coverages.return_value = {}

    # Act
    result = is_excluded_from_testing(repo_id=repo_id, filenames=[filename])

    # Assert
    assert result is False


@patch("utils.files.is_excluded_from_testing.get_coverages")
def test_is_excluded_from_testing_missing_flag(mock_get_coverages):
    # Arrange
    repo_id = 123
    filename = "missing_flag_file.py"
    mock_get_coverages.return_value = {
        filename: {"line_coverage": 80.0}  # No is_excluded_from_testing flag
    }

    # Act
    result = is_excluded_from_testing(repo_id=repo_id, filenames=[filename])

    # Assert
    assert result is False


def test_is_excluded_from_testing_empty_filename():
    # Act
    result = is_excluded_from_testing(repo_id=123, filenames=[])

    # Assert
    assert result is False
