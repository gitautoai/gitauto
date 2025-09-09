from unittest.mock import patch
from utils.files.should_test_file import should_test_file


def test_should_test_file_returns_true():
    """Test that should_test_file returns True when evaluate_condition returns True."""
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        # Arrange
        mock_evaluate.return_value = True
        file_path = "src/calculator.py"
        content = "class Calculator:\n    def add(self, a, b):\n        return a + b"
        
        # Act
        result = should_test_file(file_path, content)
        
        # Assert
        assert result is True
        mock_evaluate.assert_called_once_with(
            content=f"File path: {file_path}\n\nContent:\n{content}",
            system_prompt="""You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests.""",
        )


def test_should_test_file_returns_false():
    """Test that should_test_file returns False when evaluate_condition returns False."""
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        # Arrange
        mock_evaluate.return_value = False
        file_path = "src/constants.py"
        content = "VERSION = '1.0.0'\nAPI_URL = 'https://api.example.com'"
        
        # Act
        result = should_test_file(file_path, content)
        
        # Assert
        assert result is False
        mock_evaluate.assert_called_once_with(
            content=f"File path: {file_path}\n\nContent:\n{content}",
            system_prompt="""You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests.""",
        )


def test_should_test_file_returns_false_when_evaluate_condition_returns_none():
    """Test that should_test_file returns False when evaluate_condition returns None."""
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        # Arrange
        mock_evaluate.return_value = None
        file_path = "src/utils.py"
        content = "def helper_function():\n    pass"
        
        # Act
        result = should_test_file(file_path, content)
        
        # Assert
        assert result is False
        mock_evaluate.assert_called_once()


def test_should_test_file_handles_exception_from_evaluate_condition():
    """Test that should_test_file returns False when evaluate_condition raises an exception."""
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        # Arrange
        mock_evaluate.side_effect = Exception("API Error")
        file_path = "src/service.py"
        content = "def process_data(data):\n    return data.upper()"
        
        # Act
        result = should_test_file(file_path, content)
        
        # Assert
        assert result is False
        mock_evaluate.assert_called_once()


def test_should_test_file_with_empty_file_path():
    """Test should_test_file behavior with empty file path."""
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        # Arrange
        mock_evaluate.return_value = True
        file_path = ""
        content = "def test_function():\n    return True"
        
        # Act
        result = should_test_file(file_path, content)
        
        # Assert
        assert result is True
        mock_evaluate.assert_called_once_with(
            content=f"File path: {file_path}\n\nContent:\n{content}",
            system_prompt="""You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests.""",
        )


def test_should_test_file_with_empty_content():
    """Test should_test_file behavior with empty content."""
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        # Arrange
        mock_evaluate.return_value = False
        file_path = "src/empty.py"
        content = ""
        
        # Act
        result = should_test_file(file_path, content)
        
        # Assert
        assert result is False
        mock_evaluate.assert_called_once_with(
            content=f"File path: {file_path}\n\nContent:\n{content}",
            system_prompt="""You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests.""",
        )


def test_should_test_file_with_complex_content():
    """Test should_test_file with complex code content."""
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        # Arrange
        mock_evaluate.return_value = True
        file_path = "src/business_logic.py"
