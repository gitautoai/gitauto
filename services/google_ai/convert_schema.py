# Third-party imports
from anthropic.types.tool_param import InputSchema
from google.genai import types

# Local imports
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=False)
def convert_schema(schema: InputSchema):
    """Convert an Anthropic InputSchema to a Google-compatible Schema object.

    Removes unsupported keys like 'additionalProperties' and 'strict',
    and recursively converts nested schemas.
    """
    kwargs = {}

    type_val = schema.get("type")
    if isinstance(type_val, str):
        kwargs["type"] = type_val.upper()

    desc = schema.get("description")
    if isinstance(desc, str):
        kwargs["description"] = desc

    enum_val = schema.get("enum")
    if isinstance(enum_val, list):
        kwargs["enum"] = enum_val

    props = schema.get("properties")
    if isinstance(props, dict):
        kwargs["properties"] = {
            k: convert_schema(v) for k, v in props.items() if isinstance(v, dict)
        }

    req = schema.get("required")
    if isinstance(req, (list, tuple)):
        kwargs["required"] = list(req)

    items_val = schema.get("items")
    if isinstance(items_val, dict):
        kwargs["items"] = convert_schema(items_val)

    return types.Schema(**kwargs)
