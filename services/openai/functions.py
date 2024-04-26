# flake8: noqa
# Standard imports
from typing import Any

# Third-party imports
from openai.types import shared_params

# Local imports
from services.github.github_manager import (
    commit_multiple_changes_to_remote_branch,
    get_remote_file_content,
)

FILE_PATH: dict[str, str] = {
    "type": "string",
    "description": "The full path to the file within the repository. For example, 'src/openai/__init__.py'.",
}
OWNER: dict[str, str] = {
    "type": "string",
    "description": "The owner of the repository. For example, 'openai'.",
}
REF: dict[str, str] = {
    "type": "string",
    "description": "The ref (branch) name where the file is located. For example, 'main'.",
}
REPO: dict[str, str] = {
    "type": "string",
    "description": "The name of the repository. For example, 'openai-python'.",
}

GET_REMOTE_FILE_CONTENT: shared_params.FunctionDefinition = {
    "name": "get_remote_file_content",
    "description": "Fetches the content of a file from GitHub remote repository given the owner, repo, file_path, and ref when you need to access the file content to analyze or modify it.",
    "parameters": {
        "type": "object",
        "properties": {
            "owner": OWNER,
            "repo": REPO,
            "file_path": FILE_PATH,
            "ref": REF,
        },
        "required": ["owner", "repo", "file_path", "ref"],
    },
}


# Assistant API sometime adds a token as an input which is the reason for catchall '*args and *kwargs'
def why_modifying_diffs(why: str, *args: str, **kwargs: str) -> None:
    """Assistant API function calling to explain why it's going to modify the diffs before actually modifying the diffs."""
    print(f"\n\nWhy Agent Modifying diffs: {why}\n\n")


WHY: dict[str, str] = {
    "type": "string",
    "description": "Reason for modifying this diff",
}

WHY_MODIFYING_DIFFS: shared_params.FunctionDefinition = {
    "name": "why_modifying_diffs",
    "description": "Explain why are you modifying the diffs before you actually modify the diffs. Only argument is 'why' which is a string.",
    "parameters": {
        "type": "object",
        "properties": {"why": WHY},
        "required": ["why"],
    },
}

# Define functions
functions: dict[str, Any] = {
    "get_remote_file_content": get_remote_file_content,
    "why_modifying_diffs": why_modifying_diffs,
}
