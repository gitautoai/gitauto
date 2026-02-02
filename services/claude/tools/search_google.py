# Third-party imports
from openai.types import shared_params

# OpenAI: We recommend including instructions regarding when to call a function in the system prompt, while using the function definition to provide instructions on how to call the function and how to generate the parameters.
# https://platform.openai.com/docs/guides/function-calling/should-i-include-function-call-instructions-in-the-tool-specification-or-in-the-system-prompt

QUERY: dict[str, str] = {
    "type": "string",
    "description": "The query to search for.",
}

SEARCH_GOOGLE: shared_params.FunctionDefinition = {
    "name": "search_google",
    "description": "Search Google to verify information that may be outdated due to knowledge cutoff. Use when suggesting libraries, GitHub Actions, or external tools to: (1) Verify latest available versions (e.g., actions/checkout@v4 instead of v2). (2) Check current status of methods, tools, or parameters. NEVER search for repository-specific content - assume the repository is private.",
    "parameters": {
        "type": "object",
        "properties": {"query": QUERY},
        "required": ["query"],
        "additionalProperties": False,
    },
    "strict": True,
}
