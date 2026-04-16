# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportOptionalIterable=false, reportArgumentType=false, reportOperatorIssue=false
import json
from pathlib import Path

from services.google_ai.convert_tools import convert_tools_to_google

# Real tool definitions captured from services/claude/tools/tools.py TOOLS_FOR_SETUP
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "real_tools_for_setup.json"


def _load_real_tools():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_convert_real_tools_produces_one_tool_wrapper():
    """All 18 real tools are wrapped in a single Google Tool object."""
    tools = _load_real_tools()
    result = convert_tools_to_google(tools)
    assert len(result) == 1


def test_convert_real_tools_declaration_count():
    """All 18 real tools become 18 FunctionDeclarations."""
    tools = _load_real_tools()
    result = convert_tools_to_google(tools)
    assert len(result[0].function_declarations) == 18


def test_convert_real_tools_all_names():
    """All 18 tool names match exactly."""
    tools = _load_real_tools()
    result = convert_tools_to_google(tools)
    expected_names = [
        "apply_diff_to_file",
        "create_comment",
        "create_directory",
        "curl",
        "delete_file",
        "forget_messages",
        "git_revert_file",
        "get_local_file_tree",
        "move_file",
        "query_file",
        "run_command",
        "search_and_replace",
        "search_local_file_contents",
        "switch_node_version",
        "verify_task_is_complete",
        "web_fetch",
        "write_and_commit_file",
        "get_local_file_content",
    ]
    actual_names = [d.name for d in result[0].function_declarations]
    assert actual_names == expected_names


def test_convert_real_tools_all_descriptions_present():
    """All 18 declarations have non-empty descriptions."""
    tools = _load_real_tools()
    result = convert_tools_to_google(tools)
    for decl in result[0].function_declarations:
        assert decl.description, f"{decl.name} has empty description"


def test_convert_real_tools_apply_diff_parameters():
    """apply_diff_to_file has correct parameter schema with required fields."""
    tools = _load_real_tools()
    result = convert_tools_to_google(tools)
    decl = result[0].function_declarations[0]
    assert decl.name == "apply_diff_to_file"
    assert decl.parameters.type == "OBJECT"
    assert "file_path" in decl.parameters.properties
    assert "diff" in decl.parameters.properties
    assert decl.parameters.required == ["file_path", "diff"]
    assert decl.parameters.properties["file_path"].type == "STRING"
    assert decl.parameters.properties["diff"].type == "STRING"


def test_convert_real_tools_forget_messages_array_schema():
    """forget_messages has array property with string items."""
    tools = _load_real_tools()
    result = convert_tools_to_google(tools)
    # forget_messages is index 5
    decl = result[0].function_declarations[5]
    assert decl.name == "forget_messages"
    file_paths_prop = decl.parameters.properties["file_paths"]
    assert file_paths_prop.type == "ARRAY"
    assert file_paths_prop.items.type == "STRING"


def test_convert_real_tools_descriptions_match_input():
    """Each declaration's description matches the original tool's description."""
    tools = _load_real_tools()
    result = convert_tools_to_google(tools)
    for i, decl in enumerate(result[0].function_declarations):
        assert (
            decl.description == tools[i]["description"]
        ), f"Description mismatch for {decl.name}"


def test_convert_real_tools_empty_list():
    """Empty tools list returns empty result."""
    result = convert_tools_to_google([])
    assert not result
