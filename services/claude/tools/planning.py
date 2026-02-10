# Third-party imports
from anthropic.types import ToolUnionParam

# Local imports
from services.claude.tools.tools import (
    GET_FILE_TREE_LIST,
    GET_REMOTE_FILE_CONTENT_FULL_ONLY,
    SEARCH_LOCAL_FILE_CONTENT,
)

SUBMIT_PLAN: ToolUnionParam = {
    "name": "submit_plan",
    "description": "Call this when you have finished diagnosing the root cause and have a clear fix plan. Your plan text in the preceding message should include: the root cause, the specific files to modify, and the exact changes needed. After calling this, another agent will execute your plan.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}

TOOLS_FOR_PLANNING: list[ToolUnionParam] = [
    GET_FILE_TREE_LIST,
    GET_REMOTE_FILE_CONTENT_FULL_ONLY,
    SEARCH_LOCAL_FILE_CONTENT,
    SUBMIT_PLAN,
]
