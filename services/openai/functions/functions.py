# Standard imports
from typing import Any, Iterable

# Third-party imports
from openai.types import shared_params
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

# Local imports
from services.github.comments.update_comment import update_comment
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
from services.google.search import google_search
from services.openai.functions.properties import FILE_PATH
from services.openai.functions.search_google import SEARCH_GOOGLE
from services.openai.functions.update_comment import UPDATE_GITHUB_COMMENT
from utils.prompts.diff import DIFF_DESCRIPTION

# OpenAI: We recommend including instructions regarding when to call a function in the system prompt, while using the function definition to provide instructions on how to call the function and how to generate the parameters.
# https://platform.openai.com/docs/guides/function-calling/should-i-include-function-call-instructions-in-the-tool-specification-or-in-the-system-prompt

DIFF: dict[str, str] = {
    "type": "string",
    "description": DIFF_DESCRIPTION,
}
KEYWORD: dict[str, str] = {
    "type": "string",
    "description": "The keyword to search for in a file. For example, 'variable_name'. Exact matches only.",
}
LINE_NUMBER: dict[str, int] = {
    "type": "integer",
    "description": "If you already know the line number of interest when opening a file, use this. The 5 lines before and after this line number will be retrieved. For example, use it when checking the surrounding lines of a specific line number if the diff is incorrect.",
}

# See https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
APPLY_DIFF_TO_FILE: shared_params.FunctionDefinition = {
    "name": "apply_diff_to_file",
    "description": "Applies a diff to a file in the GitHub repository. Must be called at least once to commit the changes otherwise you can't create a pull request and resolve the issue.",
    "parameters": {
        "type": "object",
        "properties": {"file_path": FILE_PATH, "diff": DIFF},
        "required": ["file_path", "diff"],
        "additionalProperties": False,  # For Structured Outpus
    },
    "strict": True,  # For Structured Outpus
}

# See https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
GET_REMOTE_FILE_CONTENT: shared_params.FunctionDefinition = {
    "name": "get_remote_file_content",
    "description": """
    Fetches the content of a file from GitHub remote repository given file_paths when you think you need to modify the file content. NEVER EVER call this function on the same file more than once as you will be penalized critically. Only access files that are likely to require modifications or verification, and keep file access to the necessary minimum.
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
            "line_number": LINE_NUMBER,
            "keyword": KEYWORD,
        },
        "required": ["file_path"],
        # "additionalProperties": False,  # For Structured Outpus
    },
    # "strict": True,  # For Structured Outpus
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

# See https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
SEARCH_REMOTE_FILE_CONTENT: shared_params.FunctionDefinition = {
    "name": "search_remote_file_contents",
    "description": "Search for keywords in a repository to identify files and specific sections that need to be corrected. Especially if you change variable definitions, as they are likely used elsewhere, so you should search for those places. To reduce bugs, search multiple times from as many angles as possible. Must be called at least once.",
    "parameters": {
        "type": "object",
        "properties": {"query": QUERY},
        "required": ["query"],
        "additionalProperties": False,  # For Structured Outpus
    },
    "strict": True,  # For Structured Outpus
}

# See https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
GET_FILE_TREE_LIST: shared_params.FunctionDefinition = {
    "name": "get_file_tree_list",
    "description": "Lists files and directories at a specific directory path in the repository. Works like 'ls' command - shows contents of the specified directory, or root if no dir_path specified.",
    "parameters": {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Directory path to list contents of. Use empty string or omit for root directory. Examples: 'src', 'src/utils', 'tests/unit'.",
            }
        },
    },
}

# See https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
MOVE_FILE: shared_params.FunctionDefinition = {
    "name": "move_file",
    "description": "Moves a file to a new location in the GitHub repository. This is useful for resolving naming conflicts, improving code organization, or fixing pytest import collisions caused by duplicate filenames.",
    "parameters": {
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

# See https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
DELETE_FILE: shared_params.FunctionDefinition = {
    "name": "delete_file",
    "description": "Deletes a file from the GitHub repository. Use this to remove unused or duplicate files that cause conflicts.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
        },
        "required": ["file_path"],
        "additionalProperties": False,
    },
    "strict": True,
}

# See https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
TOOLS_TO_UPDATE_COMMENT: Iterable[ChatCompletionToolParam] = [
    {"type": "function", "function": UPDATE_GITHUB_COMMENT},
]
TOOLS_TO_GET_FILE: Iterable[ChatCompletionToolParam] = [
    {"type": "function", "function": GET_FILE_TREE_LIST},
    {"type": "function", "function": GET_REMOTE_FILE_CONTENT},
]
TOOLS_TO_EXPLORE_REPO: Iterable[ChatCompletionToolParam] = [
    # {"type": "code_interpreter"},
    # {"type": "retrieval"},
    {"type": "function", "function": GET_FILE_TREE_LIST},
    {"type": "function", "function": GET_REMOTE_FILE_CONTENT},
    {"type": "function", "function": SEARCH_REMOTE_FILE_CONTENT},
]
TOOLS_TO_SEARCH_GOOGLE: Iterable[ChatCompletionToolParam] = [
    {"type": "function", "function": SEARCH_GOOGLE},
]
TOOLS_TO_COMMIT_CHANGES: Iterable[ChatCompletionToolParam] = [
    {"type": "function", "function": APPLY_DIFF_TO_FILE},
    {"type": "function", "function": DELETE_FILE},
    {"type": "function", "function": MOVE_FILE},
    {"type": "function", "function": REPLACE_REMOTE_FILE_CONTENT},
]

# Define tools to call
tools_to_call: dict[str, Any] = {
    # GitHub
    "apply_diff_to_file": apply_diff_to_file,
    "delete_file": delete_file,
    "get_file_tree_list": get_file_tree_list,
    "get_remote_file_content": get_remote_file_content,
    "move_file": move_file,
    "replace_remote_file_content": replace_remote_file_content,
    "search_remote_file_contents": search_remote_file_contents,
    "update_github_comment": update_comment,
    # Google
    "search_google": google_search,
}
