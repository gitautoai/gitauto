# Standard imports
from typing import Any

# Third-party imports
from anthropic.types import ToolUnionParam

# Local imports
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.env.set_env import SET_ENV, set_env
from services.github.comments.create_comment import CREATE_COMMENT, create_comment
from services.github.comments.reply_to_comment import (
    REPLY_TO_REVIEW_COMMENT,
    reply_to_comment,
)
from services.github.commits.apply_diff_to_file import apply_diff_to_file
from services.github.commits.replace_remote_file import (
    REPLACE_REMOTE_FILE_CONTENT,
    replace_remote_file_content,
)
from services.github.files.delete_file import delete_file
from services.github.files.get_local_file_content import (
    GET_LOCAL_FILE_CONTENT,
    GET_LOCAL_FILE_CONTENT_FULL_ONLY,
    get_local_file_content,
)
from services.github.files.move_file import move_file
from services.github.search.search_local_file_contents import (
    SEARCH_LOCAL_FILE_CONTENT,
    search_local_file_contents,
)
from services.github.trees.create_directory import CREATE_DIRECTORY, create_directory
from services.github.trees.get_local_file_tree import (
    GET_LOCAL_FILE_TREE,
    get_local_file_tree,
)
from services.claude.tools.properties import FILE_PATH
from utils.prompts.diff import DIFF_DESCRIPTION

# Tool description best practices (Anthropic):
# - What the tool does, when it should be used, parameter meanings, caveats
# https://docs.anthropic.com/en/docs/build-with-claude/tool-use
# https://www.anthropic.com/engineering/writing-tools-for-agents

DIFF: dict[str, str] = {
    "type": "string",
    "description": DIFF_DESCRIPTION,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
APPLY_DIFF_TO_FILE: ToolUnionParam = {
    "name": "apply_diff_to_file",
    "description": "Applies a diff to a file in the local clone and commits the change to the PR branch.",
    "input_schema": {
        "type": "object",
        "properties": {"file_path": FILE_PATH, "diff": DIFF},
        "required": ["file_path", "diff"],
        "additionalProperties": False,
    },
    "strict": True,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
MOVE_FILE: ToolUnionParam = {
    "name": "move_file",
    "description": "Moves a file to a new location in the GitHub repository. This is useful for resolving naming conflicts, improving code organization, or fixing pytest import collisions caused by duplicate filenames.",
    "input_schema": {
        "type": "object",
        "properties": {
            "old_file_path": {
                "type": "string",
                "description": "The current path of the file to be moved. For example, 'src/old_name.py'.",
            },
            "new_file_path": {
                "type": "string",
                "description": "The new path for the file. For example, 'src/new_name.py'. Must be different from old_file_path.",
            },
        },
        "required": ["old_file_path", "new_file_path"],
        "additionalProperties": False,
    },
    "strict": True,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
DELETE_FILE: ToolUnionParam = {
    "name": "delete_file",
    "description": "Deletes a file from the GitHub repository. Use this to remove unused or duplicate files that cause conflicts.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
        },
        "required": ["file_path"],
        "additionalProperties": False,
    },
    "strict": True,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
# No parameters needed - agent calls with empty {} (JSON Schema requires the object structure)
# In API payload: verify_task_is_complete({}) - the empty object must be explicitly sent
# Conceptually equivalent to verify_task_is_complete() - a function with no arguments
VERIFY_TASK_IS_COMPLETE: ToolUnionParam = {
    "name": "verify_task_is_complete",
    "description": "Call this when you have finished making all required changes for the ENTIRE original issue - not after just one step. You MUST call this to complete the task - do not just stop calling tools.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


_TOOLS_BASE: list[ToolUnionParam] = [
    APPLY_DIFF_TO_FILE,
    CREATE_COMMENT,
    CREATE_DIRECTORY,
    DELETE_FILE,
    GET_LOCAL_FILE_TREE,
    MOVE_FILE,
    REPLACE_REMOTE_FILE_CONTENT,
    SEARCH_LOCAL_FILE_CONTENT,
    VERIFY_TASK_IS_COMPLETE,
]

TOOLS_FOR_ISSUES: list[ToolUnionParam] = _TOOLS_BASE + [
    GET_LOCAL_FILE_CONTENT,
    SET_ENV,
]

# PR handlers need full file reads (no partial read options)
TOOLS_FOR_PRS: list[ToolUnionParam] = _TOOLS_BASE + [
    GET_LOCAL_FILE_CONTENT_FULL_ONLY,
    SET_ENV,
]

# Review comment handler adds reply capability
TOOLS_FOR_REVIEW_COMMENTS: list[ToolUnionParam] = TOOLS_FOR_PRS + [
    REPLY_TO_REVIEW_COMMENT,
]

# Setup handler reads project files to detect language/framework, then creates workflow files
TOOLS_FOR_SETUP: list[ToolUnionParam] = _TOOLS_BASE + [
    GET_LOCAL_FILE_CONTENT,
]

FILE_EDIT_TOOLS = [
    "apply_diff_to_file",
    "replace_remote_file_content",
    "move_file",
    "delete_file",
]

# Define tools to call
tools_to_call: dict[str, Any] = {
    # GitHub
    "apply_diff_to_file": apply_diff_to_file,
    "create_comment": create_comment,
    "create_directory": create_directory,
    "delete_file": delete_file,
    "get_local_file_content": get_local_file_content,
    "get_local_file_tree": get_local_file_tree,
    "move_file": move_file,
    "replace_remote_file_content": replace_remote_file_content,
    "reply_to_review_comment": reply_to_comment,
    "search_local_file_contents": search_local_file_contents,
    "set_env": set_env,
    "verify_task_is_complete": verify_task_is_complete,
}
