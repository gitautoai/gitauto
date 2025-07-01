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