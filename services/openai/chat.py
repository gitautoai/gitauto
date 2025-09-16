# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Local imports
from config import OPENAI_MODEL_ID_GPT_5
from services.openai.init import create_openai_client
from services.openai.truncate import truncate_message
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_ai(system_input: str, user_input: str) -> str:
    """https://platform.openai.com/docs/api-reference/chat/create"""
    client: OpenAI = create_openai_client()
    truncated_msg: str = truncate_message(input_message=user_input)
    completion: ChatCompletion = client.chat.completions.create(
        messages=[
            {
                "role": "developer",
                "content": system_input,
            },
            {
                "role": "user",
                "content": truncated_msg if truncated_msg else user_input,
            },
        ],
        model=OPENAI_MODEL_ID_GPT_5,
    )
    content: str | None = completion.choices[0].message.content
    response: str = content if content else ""
    return response
