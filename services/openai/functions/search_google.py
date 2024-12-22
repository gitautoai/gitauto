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
    "description": "Search Google for a query.",
    "parameters": {
        "type": "object",
        "properties": {"query": QUERY},
        "required": ["query"],
        "additionalProperties": False,
    },
}
