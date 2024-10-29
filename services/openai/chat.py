# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Local imports
from config import OPENAI_MODEL_ID_O1_MINI
from services.openai.init import create_openai_client
from services.openai.truncate import truncate_message
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_ai(system_input: str, user_input: str) -> str:
    """https://platform.openai.com/docs/api-reference/chat/create"""
    client: OpenAI = create_openai_client()
    truncated_msg: str = truncate_message(input_message=user_input)
    completion: ChatCompletion = client.chat.completions.create(
        messages=[
            {
                "role": "user",  # role should be system but it is not allowed for 01-mini as of Oct 5 2024. https://community.openai.com/t/o1-models-do-not-support-system-role-in-chat-completion/953880/2
                "content": system_input,
            },
            {
                "role": "user",
                "content": truncated_msg if truncated_msg else user_input,
            },
        ],
        model=OPENAI_MODEL_ID_O1_MINI,
        n=1,
        # temperature=OPENAI_TEMPERATURE,  # temperature should be 0 but it is not supported for 01-mini as of Oct 5 2024
    )
    content: str | None = completion.choices[0].message.content
    response: str = content if content else ""

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
