# Third-party imports
from anthropic.types import ToolUnionParam
from google.genai import types

# Local imports
from services.google_ai.convert_schema import convert_schema
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def convert_tools_to_google(
    tools: list[ToolUnionParam],
):
    """Convert Anthropic tool definitions to Google FunctionDeclaration format.
    Anthropic: {name, description, input_schema} -> Google: FunctionDeclaration(name, description, parameters).
    Strips unsupported JSON Schema keys (additionalProperties, strict)."""
    declarations: list[types.FunctionDeclaration] = []

    for tool in tools:
        if not isinstance(tool, dict):
            continue
        # Only ToolParam (custom tools) have input_schema; skip bash/text_editor
        if "input_schema" not in tool:
            continue
        name = tool["name"]
        description = tool.get("description")
        input_schema = tool["input_schema"]
        parameters = convert_schema(input_schema) if input_schema else None

        declarations.append(
            types.FunctionDeclaration(
                name=name,
                description=description if isinstance(description, str) else "",
                parameters=parameters,
            )
        )

    return [types.Tool(function_declarations=declarations)] if declarations else []
