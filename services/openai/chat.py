# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Local imports
from config import OPENAI_API_KEY, OPENAI_MODEL_ID, OPENAI_ORG_ID, OPENAI_TEMPERATURE
from services.openai.instructions import SYSTEM_INSTRUCTION_FOR_WRITING_PR


# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)


def write_pr_body(input_message: str) -> str:
    try:
        completion: ChatCompletion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION_FOR_WRITING_PR},
                {"role": "user", "content": input_message}
            ],
            model=OPENAI_MODEL_ID,
            n=1,
            temperature=OPENAI_TEMPERATURE,
        )
        content: str | None = completion.choices[0].message.content
        response: str = content if content else "No response from OpenAI"
        print(f"OpenAI response: {response}")
        return response
    except Exception as e:
        raise ValueError(f"Error: {e}") from e
