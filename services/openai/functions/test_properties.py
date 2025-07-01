# Standard imports
import pytest
import json

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


def test_file_path_property_as_json_schema():
    """Test that FILE_PATH follows JSON Schema property structure."""
    # Verify the property has the minimum required fields for a JSON Schema property
    assert "type" in FILE_PATH
    # Verify the type is a valid JSON Schema type
    assert FILE_PATH["type"] in ["string", "number", "integer", "boolean", "array", "object", "null"]


def test_file_path_in_json_schema_context():
    """Test that FILE_PATH can be used in a JSON Schema context."""
    # Create a simple JSON Schema that uses FILE_PATH
    schema = {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH
        },
        "required": ["file_path"]
    }
    
    # Verify the schema is valid JSON
    json_str = json.dumps(schema)
    parsed_schema = json.loads(json_str)
    
    # Verify the FILE_PATH property was correctly included in the schema
    assert "file_path" in parsed_schema["properties"]
    assert parsed_schema["properties"]["file_path"]["type"] == "string"
    assert "description" in parsed_schema["properties"]["file_path"]


def test_file_path_in_function_definition():
    """Test that FILE_PATH can be used in an OpenAI function definition."""
    # Create a function definition that uses FILE_PATH
    function_def = {
        "name": "get_remote_file_content",
        "description": "Get content of a remote file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": FILE_PATH
            },
            "required": ["file_path"]
        }
    }
    
    # Verify the function definition is valid JSON
    json_str = json.dumps(function_def)
    parsed_function = json.loads(json_str)
    
    # Verify the FILE_PATH property was correctly included in the function definition
    assert "parameters" in parsed_function
    assert "properties" in parsed_function["parameters"]
    assert "file_path" in parsed_function["parameters"]["properties"]
    assert parsed_function["parameters"]["properties"]["file_path"]["type"] == "string"
    assert "description" in parsed_function["parameters"]["properties"]["file_path"]