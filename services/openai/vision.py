# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Local imports
from config import OPENAI_MODEL_ID_GPT_5
from services.openai.init import create_openai_client
from utils.error.handle_exceptions import handle_exceptions
from utils.prompts.describe_image import DESCRIBE_IMAGE


@handle_exceptions(default_return_value="", raise_on_error=False)
def describe_image(base64_image: str, context: str | None = None) -> str:
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
                    {"type": "text", "text": DESCRIBE_IMAGE},
                    *(
                        [{"type": "text", "text": context}]
                        if context is not None
                        else []
                    ),
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
        model=OPENAI_MODEL_ID_GPT_5,
        n=1,
        # temperature=OPENAI_TEMPERATURE,  # GPT-5 only supports default temperature (1)
    )
    message_content = completion.choices[0].message.content
    content: str | None = message_content.strip() if message_content else None
    description: str = content if content else "No response from OpenAI"
    return description
