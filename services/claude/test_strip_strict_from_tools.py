from typing import cast

from anthropic.types import ToolUnionParam

from services.claude.strip_strict_from_tools import strip_strict_from_tools


def test_strips_strict_key_from_tools():
    # cast: test fixtures satisfying ToolUnionParam union type
    tools = [
        cast(
            ToolUnionParam,
            {
                "name": "tool1",
                "description": "desc",
                "input_schema": {"type": "object", "properties": {}},
                "strict": True,
            },
        ),
        cast(
            ToolUnionParam,
            {
                "name": "tool2",
                "description": "desc",
                "input_schema": {"type": "object", "properties": {}},
            },
        ),
    ]
    result = strip_strict_from_tools(tools)
    assert "strict" not in result[0]
    assert result[0]["name"] == "tool1"
    assert "strict" not in result[1]
    assert result[1]["name"] == "tool2"


def test_does_not_mutate_originals():
    # cast: test fixture satisfying ToolUnionParam union type
    tools = [
        cast(
            ToolUnionParam,
            {
                "name": "tool1",
                "description": "desc",
                "input_schema": {"type": "object", "properties": {}},
                "strict": True,
            },
        ),
    ]
    strip_strict_from_tools(tools)
    assert "strict" in tools[0]


def test_empty_tools():
    assert not strip_strict_from_tools([])
