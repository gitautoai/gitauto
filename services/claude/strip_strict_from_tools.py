from typing import cast

from anthropic.types import ToolUnionParam

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda tools: tools, raise_on_error=False)
def strip_strict_from_tools(tools: list[ToolUnionParam]):
    """Remove 'strict' key from tool definitions for models that don't support it."""
    cleaned: list[ToolUnionParam] = []
    for tool in tools:
        if isinstance(tool, dict) and "strict" in tool:
            # cast: dict comprehension produces valid ToolParam but pyright can't verify against ToolUnionParam union
            tool_copy = cast(
                ToolUnionParam, {k: v for k, v in tool.items() if k != "strict"}
            )
            cleaned.append(tool_copy)
        else:
            cleaned.append(tool)
    return cleaned
