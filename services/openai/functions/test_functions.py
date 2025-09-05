import inspect
from services.openai.functions import functions


def test_function_schemas_strict_mode_validation():
    """Test that all function schemas with strict=True have all properties in required array (AGENT-126 regression test)"""

    # Dynamically discover all FunctionDefinition objects in the functions module
    function_definitions = []
    for name, obj in inspect.getmembers(functions):
        if isinstance(obj, dict) and "name" in obj and "parameters" in obj:
            function_definitions.append((name, obj))

    for var_name, func_def in function_definitions:
        func_name = func_def["name"]
        parameters = func_def["parameters"]
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])
        is_strict = func_def.get("strict", False)

        if is_strict:
            # When strict=True, all properties must be in required array
            property_keys = set(properties.keys())
            required_keys = set(required)

            missing_required = property_keys - required_keys
            assert not missing_required, (
                f"Function '{func_name}' (variable: {var_name}) has strict=True but properties {missing_required} "
                f"are not in required array. This causes OpenAI API validation error (AGENT-126 type failure)."
            )


def test_get_file_tree_list_schema_allows_optional_dir_path():
    """Test that get_file_tree_list schema correctly allows optional dir_path parameter"""
    schema = functions.GET_FILE_TREE_LIST

    # Should not have strict=True since dir_path is optional
    assert not schema.get(
        "strict"
    ), "get_file_tree_list should not use strict=True because dir_path is optional"

    # Should have dir_path in properties
    parameters = schema.get("parameters", {})
    properties = parameters.get("properties", {})
    assert isinstance(properties, dict), "properties should be a dict"
    assert "dir_path" in properties, "dir_path should be defined in properties"

    # dir_path should not be required (or required array should be empty/not include it)
    required = parameters.get("required", [])
    assert isinstance(required, list), "required should be a list"
    assert (
        "dir_path" not in required
    ), "dir_path should not be in required array since it has default value"


def test_all_strict_functions_have_valid_schemas():
    """Test that functions with strict=True have proper schema structure"""

    # Dynamically discover all FunctionDefinition objects
    function_definitions = []
    for name, obj in inspect.getmembers(functions):
        if isinstance(obj, dict) and "name" in obj and "parameters" in obj:
            function_definitions.append((name, obj))

    for var_name, func_def in function_definitions:
        if func_def.get("strict"):
            func_name = func_def["name"]
            parameters = func_def["parameters"]

            # Must have additionalProperties=False when strict=True
            assert (
                parameters.get("additionalProperties") is False
            ), f"Function '{func_name}' (variable: {var_name}) with strict=True must have additionalProperties=False"

            # Must have all properties in required array
            properties = parameters.get("properties", {})
            required = parameters.get("required", [])

            assert len(required) == len(
                properties
            ), f"Function '{func_name}' (variable: {var_name}) with strict=True must have all properties in required array"


def test_function_schema_discovery():
    """Test that we can discover function definitions dynamically"""
    function_definitions = []
    for name, obj in inspect.getmembers(functions):
        if isinstance(obj, dict) and "name" in obj and "parameters" in obj:
            function_definitions.append(name)

    # Should find at least the known functions
    expected_functions = [
        "GET_FILE_TREE_LIST",
        "APPLY_DIFF_TO_FILE",
        "GET_REMOTE_FILE_CONTENT",
    ]
    for expected in expected_functions:
        assert (
            expected in function_definitions
        ), f"Expected to find {expected} in discovered functions"
