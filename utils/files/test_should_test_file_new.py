import pytest
from unittest.mock import patch

from utils.files.should_test_file import should_test_file


class TestShouldTestFile:
    """Test cases for should_test_file function."""

    @pytest.fixture
    def mock_evaluate_condition(self):
        """Mock the evaluate_condition function."""
        with patch("utils.files.should_test_file.evaluate_condition") as mock:
            yield mock

    @pytest.fixture
    def sample_file_path(self):
        """Sample file path for testing."""
        return "src/utils/helper.py"

    @pytest.fixture
    def sample_code_content(self):
        """Sample code content for testing."""
        return """
def calculate_sum(a, b):
    return a + b

def validate_input(value):
    if not isinstance(value, int):
        raise ValueError("Input must be an integer")
    return True
"""

    def test_should_test_file_returns_true_when_evaluate_condition_returns_true(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test function returns True when evaluate_condition returns True."""
        mock_evaluate_condition.return_value = True

        result = should_test_file(sample_file_path, sample_code_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_returns_false_when_evaluate_condition_returns_none(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test function returns False when evaluate_condition returns None."""
        mock_evaluate_condition.return_value = None

        result = should_test_file(sample_file_path, sample_code_content)

        assert result is False
        mock_evaluate_condition.assert_called_once()
