# Standard imports
from typing import Any

# Third-party imports
from openai.types import shared_params

# Local imports
from services.github.github_manager import (
    commit_changes_to_remote_branch,
    get_remote_file_content,
    search_remote_file_contents,
)
from services.openai.instructions.diff import DIFF_DESCRIPTION

# OpenAI: We recommend including instructions regarding when to call a function in the system prompt, while using the function definition to provide instructions on how to call the function and how to generate the parameters.
# https://platform.openai.com/docs/guides/function-calling/should-i-include-function-call-instructions-in-the-tool-specification-or-in-the-system-prompt

DIFF: dict[str, str] = {
    "type": "string",
    "description": DIFF_DESCRIPTION,
}
FILE_PATH: dict[str, str] = {
    "type": "string",
    "description": "The full path to the file within the repository. For example, 'src/openai/__init__.py'. NEVER EVER be the same as the file_path in previous function calls.",
}
KEYWORD: dict[str, str] = {
    "type": "string",
    "description": "The keyword to search for in a file. For example, 'variable_name'. Exact matches only.",
}
LINE_NUMBER: dict[str, int] = {
    "type": "integer",
    "description": "If you already know the line number of interest when opening a file, use this. The 5 lines before and after this line number will be retrieved. For example, use it when checking the surrounding lines of a specific line number if the diff is incorrect.",
}

COMMIT_CHANGES_TO_REMOTE_BRANCH: shared_params.FunctionDefinition = {
    "name": "commit_changes_to_remote_branch",
    "description": "Commits the changes to the remote branch in the GitHub repository. Must be called at least once to commit the changes otherwise you can't create a pull request and resolve the issue.",
    "parameters": {
        "type": "object",
        "properties": {"file_path": FILE_PATH, "diff": DIFF},
        "required": ["file_path", "diff"],
        "additionalProperties": False,  # For Structured Outpus
    },
    "strict": True,  # For Structured Outpus
}

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
    """,
}
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

# Define functions
functions: dict[str, Any] = {
    "commit_changes_to_remote_branch": commit_changes_to_remote_branch,
    "get_remote_file_content": get_remote_file_content,
    "search_remote_file_contents": search_remote_file_contents,
}
