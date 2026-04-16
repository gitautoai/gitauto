# pyright: reportArgumentType=false, reportOperatorIssue=false, reportOptionalMemberAccess=false
from services.google_ai.convert_schema import convert_schema


def test_simple_string_schema():
    schema = {"type": "string", "description": "A name"}
    result = convert_schema(schema)
    assert result.type == "STRING"
    assert result.description == "A name"


def test_object_with_properties():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name"},
            "age": {"type": "integer", "description": "Age"},
        },
        "required": ["name"],
    }
    result = convert_schema(schema)
    assert result.type == "OBJECT"
    assert "name" in result.properties
    assert "age" in result.properties
    assert result.required == ["name"]


def test_array_with_items():
    schema = {
        "type": "array",
        "items": {"type": "string"},
    }
    result = convert_schema(schema)
    assert result.type == "ARRAY"
    assert result.items.type == "STRING"


def test_enum_values():
    schema = {"type": "string", "enum": ["a", "b", "c"]}
    result = convert_schema(schema)
    assert result.enum == ["a", "b", "c"]


def test_strips_unsupported_keys():
    schema = {
        "type": "object",
        "additionalProperties": False,
        "strict": True,
        "properties": {"x": {"type": "string"}},
    }
    result = convert_schema(schema)
    assert result.type == "OBJECT"
    assert "x" in result.properties
