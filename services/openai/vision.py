# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Local imports
from config import OPENAI_MODEL_ID, OPENAI_TEMPERATURE
from services.openai.init import create_openai_client
from services.openai.instructions.index import USER_INSTRUCTION
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=None)
def describe_image(base64_image: str) -> str:
    """
    1. API doc: https://platform.openai.com/docs/api-reference/chat/create
    2. 20MB per image is allowed: https://platform.openai.com/docs/guides/vision/is-there-a-limit-to-the-size-of-the-image-i-can-upload
    3. PNG (.png), JPEG (.jpeg and .jpg), WEBP (.webp), and non-animated GIF (.gif) are only supported: https://platform.openai.com/docs/guides/vision/what-type-of-files-can-i-upload
    """
    client: OpenAI = create_openai_client()
    completion: ChatCompletion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": USER_INSTRUCTION,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "auto",
                        },
                    },
                ],
            },
        ],
        model=OPENAI_MODEL_ID,
        n=1,
        temperature=OPENAI_TEMPERATURE,
    )
    content: str | None = completion.choices[0].message.content.strip()
    description: str = content if content else "No response from OpenAI"
    return description
