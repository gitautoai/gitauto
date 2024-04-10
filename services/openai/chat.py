# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Local imports
from config import OPENAI_MODEL_ID, OPENAI_TEMPERATURE
from services.openai.init import create_openai_client
from services.openai.instructions import SYSTEM_INSTRUCTION_FOR_WRITING_PR


def write_pr_body(input_message: str) -> str:
    """https://platform.openai.com/docs/api-reference/chat/create"""
    try:
        client: OpenAI = create_openai_client()
        completion: ChatCompletion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION_FOR_WRITING_PR},
                {"role": "user", "content": input_message},
            ],
            model=OPENAI_MODEL_ID,
            n=1,
            temperature=OPENAI_TEMPERATURE,
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

        print(f"OpenAI response: {response}")
        return response
    except Exception as e:
        raise ValueError(f"Error: {e}") from e
