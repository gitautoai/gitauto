# Standard imports
import pytest

# Local imports
from services.openai.functions.properties import FILE_PATH


def test_file_path_property_structure():
    """Test that FILE_PATH dictionary has the correct structure and values."""
    # Verify the dictionary has the expected keys
    assert "type" in FILE_PATH
    assert "description" in FILE_PATH
    
    # Verify the values are correct
    assert FILE_PATH["type"] == "string"
    assert "The full path to the file within the repository" in FILE_PATH["description"]


def test_file_path_property_warning():
    """Test that FILE_PATH description contains the important warning about not reusing file paths."""
    # Verify the description contains the warning about not reusing file paths
    assert "NEVER EVER be the same as the file_path in previous function calls" in FILE_PATH["description"]
    
    # Verify the description includes an example for clarity
    assert "For example" in FILE_PATH["description"]
    assert "src/openai/__init__.py" in FILE_PATH["description"]