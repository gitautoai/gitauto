from openai.types.beta.assistant_create_params import ToolAssistantToolsFunction

FILE_PATH: dict[str, str] = {
    "type": "string",
    "description": "The full path to the file within the repository. For example, 'src/openai/__init__.py'."
}
OWNER: dict[str, str] = {
    "type": "string",
    "description": "The owner of the repository. For example, 'openai'."
}
REF: dict[str, str] = {
    "type": "string",
    "description": "The ref (branch) name where the file is located. For example, 'main'."
}
REPO: dict[str, str] = {
    "type": "string",
    "description": "The name of the repository. For example, 'openai-python'."
}

get_remote_file_content: ToolAssistantToolsFunction = {
    "type": "function",
    "function": {
        "name": "get_remote_file_content",
        "description": "Fetches the content of a file from GitHub remote repository given the owner, repo, file_path, and ref.",
        "parameters": {
            "type": "object",
            "properties": {
                "owner": OWNER,
                "repo": REPO,
                "file_path": FILE_PATH,
                "ref": REF
            },
            "required": ["owner", "repo", "file_path", "ref"]
        },
    }
}
