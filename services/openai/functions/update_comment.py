# Third-party imports
from openai.types import shared_params

# OpenAI: We recommend including instructions regarding when to call a function in the system prompt, while using the function definition to provide instructions on how to call the function and how to generate the parameters.
# https://platform.openai.com/docs/guides/function-calling/should-i-include-function-call-instructions-in-the-tool-specification-or-in-the-system-prompt

BODY: dict[str, str] = {
    "type": "string",
    "description": "The body of the comment.",
}

UPDATE_GITHUB_COMMENT: shared_params.FunctionDefinition = {
    "name": "update_github_comment",
    "description": "Updates a comment in GitHub issue or GitHub pull request.",
    "parameters": {
        "type": "object",
        "properties": {"body": BODY},
        "required": ["body"],
        "additionalProperties": False,
    },
    "strict": True,
}
