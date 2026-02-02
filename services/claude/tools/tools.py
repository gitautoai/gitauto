# Standard imports
from typing import Any

# Third-party imports
from anthropic.types import ToolUnionParam

# Local imports
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.github.comments.create_comment import create_comment
from services.github.commits.apply_diff_to_file import apply_diff_to_file
from services.github.commits.replace_remote_file import (
    REPLACE_REMOTE_FILE_CONTENT,
    replace_remote_file_content,
)
from services.github.files.delete_file import delete_file
from services.github.files.get_remote_file_content import get_remote_file_content
from services.github.files.move_file import move_file
from services.github.search.search_remote_file_contents import (
    search_remote_file_contents,
)
from services.github.trees.get_file_tree_list import get_file_tree_list
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
KEYWORD: dict[str, str] = {
    "type": "string",
    "description": "The keyword to search for in a file. For example, 'variable_name'. Exact matches only.",
}
LINE_NUMBER: dict[str, str] = {
    "type": "integer",
    "description": "If you already know the line number of interest when opening a file, use this. The 5 lines before and after this line number will be retrieved. For example, use it when checking the surrounding lines of a specific line number if the diff is incorrect. Cannot be used with start_line/end_line.",
}
START_LINE: dict[str, str] = {
    "type": "integer",
    "description": "Starting line number for a specific range of lines to retrieve from the file. If end_line is not provided, will retrieve from start_line to end of file.",
}
END_LINE: dict[str, str] = {
    "type": "integer",
    "description": "Ending line number for a specific range of lines to retrieve from the file. If start_line is not provided, will retrieve from beginning of file to end_line.",
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
APPLY_DIFF_TO_FILE: ToolUnionParam = {
    "name": "apply_diff_to_file",
    "description": "Applies a diff to a file in the GitHub repository. Must be called at least once to commit the changes otherwise you can't create a pull request and resolve the issue.",
    "input_schema": {
        "type": "object",
        "properties": {"file_path": FILE_PATH, "diff": DIFF},
        "required": ["file_path", "diff"],
        "additionalProperties": False,
    },
    "strict": True,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
# NOTE: No strict=True here because line_number, keyword, start_line, end_line are optional
GET_REMOTE_FILE_CONTENT: ToolUnionParam = {
    "name": "get_remote_file_content",
    "description": """
    Fetches the content of a file from GitHub remote repository given file_paths when you think you need to modify the file content. NEVER EVER call this function on the same file more than once as you will be penalized critically. Only access files that are likely to require modifications or verification, and keep file access to the necessary minimum.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
            "line_number": LINE_NUMBER,
            "keyword": KEYWORD,
            "start_line": START_LINE,
            "end_line": END_LINE,
        },
        "required": ["file_path"],
        "additionalProperties": False,
    },
}

QUERY: dict[str, str] = {
    "type": "string",
    "description": """
    The keywords to search for in the remote repository. For example, 'SEARCH_KEYWORD_1 SEARCH_KEYWORD_N QUALIFIER_1 QUALIFIER_N'. But realistically, you should search for a specific variable name, function name, or other unique identifier not multiple keywords because seaarching for more than one keyword may not be effective.

    ## Good Query Examples

    - Search for a specific variable name: 'variable_name'
    - Search for a specific function name: 'function_name'
    - Search for a specific class name: 'class_name'
    - Search for a specific keyword: 'keyword'

    ## Bad Query Examples

    - Search for multiple variables at once: 'variable_name_1 variable_name_2'
    - Search for multiple functions at once: 'function_name_1 function_name_2'
    - Search for an entire line of code: 'from module import function_name'

    ## Important Note

    You can narrow down search results by excluding one or more subsets. To exclude all results that are matched by a qualifier, prefix the search qualifier with a hyphen (-). However, be careful when searching for command options like '--xxxxxx' because this results in `ERROR_TYPE_QUERY_PARSING_FATAL unable to parse query!`

    When searching for command-line options:
    - Search for 'config' instead of '--config'
    - Search for 'verbose' instead of '--verbose'
    """,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
SEARCH_REMOTE_FILE_CONTENT: ToolUnionParam = {
    "name": "search_remote_file_contents",
    "description": "Search for keywords in a repository to identify files and specific sections that need to be corrected. Especially if you change variable definitions, as they are likely used elsewhere, so you should search for those places. To reduce bugs, search multiple times from as many angles as possible. Must be called at least once.",
    "input_schema": {
        "type": "object",
        "properties": {"query": QUERY},
        "required": ["query"],
        "additionalProperties": False,
    },
    "strict": True,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
# NOTE: No strict=True here because dir_path is optional (not in required list)
GET_FILE_TREE_LIST: ToolUnionParam = {
    "name": "get_file_tree_list",
    "description": "Lists files and directories at a specific directory path in the repository. Works like 'ls' command - shows contents of the specified directory, or root if no dir_path specified.",
    "input_schema": {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Directory path to list contents of. Use empty string or omit for root directory. Examples: 'src', 'src/utils', 'tests/unit'.",
            }
        },
        "additionalProperties": False,
    },
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

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
CREATE_COMMENT: ToolUnionParam = {
    "name": "create_comment",
    "description": "Creates a note/notification on the GitHub issue or pull request. The user is not there - they will see it later. After commenting, continue working on what you CAN do. WHEN TO USE: To inform the user about something they need to know (e.g., you are restricted to test files but the fix requires source file changes, or secrets need to be added via GitHub UI). WHEN NOT TO USE: Status updates, progress reports, or asking questions. WHAT TO SAY: State the fact briefly - what you found and what the user needs to do later. Do not ask questions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "body": {
                "type": "string",
                "description": "The comment text to post.",
            },
        },
        "required": ["body"],
        "additionalProperties": False,
    },
    "strict": True,
}

_TOOLS: list[ToolUnionParam] = [
    APPLY_DIFF_TO_FILE,
    CREATE_COMMENT,
    DELETE_FILE,
    GET_FILE_TREE_LIST,
    GET_REMOTE_FILE_CONTENT,
    MOVE_FILE,
    REPLACE_REMOTE_FILE_CONTENT,
    VERIFY_TASK_IS_COMPLETE,
]

TOOLS_FOR_ISSUES: list[ToolUnionParam] = _TOOLS + [
    SEARCH_REMOTE_FILE_CONTENT,
]

# search_remote_file_contents only searches default branch, not PR branch
TOOLS_FOR_PRS: list[ToolUnionParam] = _TOOLS + [
    # TODO: Add search_local_file_contents when implemented
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
    "delete_file": delete_file,
    "get_file_tree_list": get_file_tree_list,
    "get_remote_file_content": get_remote_file_content,
    "move_file": move_file,
    "replace_remote_file_content": replace_remote_file_content,
    # "search_google": google_search,
    "search_remote_file_contents": search_remote_file_contents,
    "verify_task_is_complete": verify_task_is_complete,
}
