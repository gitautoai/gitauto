# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Local imports
from config import OPENAI_MODEL_ID_O1_PREVIEW
from services.openai.init import create_openai_client
from services.openai.instructions.write_pr_body import WRITE_PR_BODY
from services.openai.truncate import truncate_message
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def write_pr_body(input_message: str) -> str:
    """https://platform.openai.com/docs/api-reference/chat/create"""
    client: OpenAI = create_openai_client()
    truncated_msg: str = truncate_message(input_message=input_message)
    completion: ChatCompletion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": WRITE_PR_BODY},  # role should be system but it is not allowed for 01-mini as of Oct 5 2024. https://community.openai.com/t/o1-models-do-not-support-system-role-in-chat-completion/953880/2
            {
                "role": "user",
                "content": truncated_msg if truncated_msg else input_message,
            },
        ],
        model=OPENAI_MODEL_ID_O1_PREVIEW,
        n=1,
        # temperature=OPENAI_TEMPERATURE,  # temperature should be 0 but it is not supported for 01-mini as of Oct 5 2024
    )
    content: str | None = completion.choices[0].message.content
    response: str = content if content else "No response from OpenAI"

    # Check for backticks
    if response[:4] == "```\n":
        response = response[4:]
    if response[:3] == "```":
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]

    # Check for triple quotes
    if response[:4] == '"""\n':
        response = response[4:]
    if response[:3] == '"""\n':
        response = response[3:]
    if response.endswith('"""'):
        response = response[:-3]

    return response
