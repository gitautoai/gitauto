# pylint: disable=protected-access
import inspect

from services.claude.file_tracking import FILE_EDIT_TOOLS
from services.claude.tools import tools


def test_function_schemas_strict_mode_validation():
    """Test that all function schemas with strict=True have all properties in required array (AGENT-126 regression test)"""

    # Dynamically discover all FunctionDefinition objects in the tools module
    function_definitions = []
    for name, obj in inspect.getmembers(tools):
        if isinstance(obj, dict) and "name" in obj and "input_schema" in obj:
            function_definitions.append((name, obj))

    for var_name, func_def in function_definitions:
        func_name = func_def["name"]
        input_schema = func_def["input_schema"]
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
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


def test_get_local_file_tree_schema_allows_optional_dir_path():
    """Test that get_local_file_tree schema correctly allows optional dir_path parameter"""
    schema = tools.GET_LOCAL_FILE_TREE

    # Should not have strict=True since dir_path is optional
    assert not schema.get(
        "strict"
    ), "get_local_file_tree should not use strict=True because dir_path is optional"

    # dir_path should be the only property, and it should be optional (not required)
    input_schema = schema.get("input_schema")
    assert isinstance(input_schema, dict)
    properties = input_schema.get("properties")
    assert isinstance(properties, dict)
    assert set(properties.keys()) == {"dir_path"}
    required = input_schema.get("required")
    assert required is None or required == []


def test_all_strict_tools_have_valid_schemas():
    """Test that tools with strict=True have proper schema structure"""

    # Dynamically discover all FunctionDefinition objects
    function_definitions = []
    for name, obj in inspect.getmembers(tools):
        if isinstance(obj, dict) and "name" in obj and "input_schema" in obj:
            function_definitions.append((name, obj))

    for var_name, func_def in function_definitions:
        if func_def.get("strict"):
            func_name = func_def["name"]
            input_schema = func_def["input_schema"]

            # Must have additionalProperties=False when strict=True
            assert (
                input_schema.get("additionalProperties") is False
            ), f"Function '{func_name}' (variable: {var_name}) with strict=True must have additionalProperties=False"

            # Must have all properties in required array
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])

            assert len(required) == len(
                properties
            ), f"Function '{func_name}' (variable: {var_name}) with strict=True must have all properties in required array"


def test_file_edit_tools_moved_to_file_tracking():
    # FILE_EDIT_TOOLS was moved from tools.py to file_tracking.py to avoid circular import
    assert not hasattr(tools, "FILE_EDIT_TOOLS")
    # Every edit tool must be dispatchable
    for tool_name in FILE_EDIT_TOOLS:
        assert (
            tools.tools_to_call.get(tool_name) is not None
        ), f"{tool_name} missing from tools_to_call"


def test_git_diff_in_base_tools():
    # git_diff should be available in all tool sets
    assert tools.GIT_DIFF["name"] == "git_diff"
    # GIT_DIFF must be one of the base tools
    matched = [t for t in tools._TOOLS_BASE if t["name"] == "git_diff"]
    assert len(matched) == 1


def test_git_diff_in_dispatch():
    # git_diff must be in tools_to_call dispatch dict
    assert tools.tools_to_call.get("git_diff") is not None


def test_function_schema_discovery():
    """Test that we can discover function definitions dynamically"""
    function_definitions = []
    for name, obj in inspect.getmembers(tools):
        if isinstance(obj, dict) and "name" in obj and "input_schema" in obj:
            function_definitions.append(name)

    # Should find at least the known tools
    expected_tools = [
        "GET_LOCAL_FILE_TREE",
        "APPLY_DIFF_TO_FILE",
        "GET_LOCAL_FILE_CONTENT",
    ]
    for expected in expected_tools:
        assert (
            expected in function_definitions
        ), f"Expected to find {expected} in discovered tools"
