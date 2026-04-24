# Standard imports
import time

# Third-party imports
from openai import OpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
)

# Local imports
from config import OPENAI_MODEL_ID
from services.openai.init import create_openai_client
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.prompts.describe_image import DESCRIBE_IMAGE


@handle_exceptions(default_return_value="", raise_on_error=False)
def describe_image(
    base64_image: str,
    usage_id: int,
    created_by: str,
    context: str | None = None,
):
    """
    1. API doc: https://platform.openai.com/docs/api-reference/chat/create
    2. 20MB per image is allowed: https://platform.openai.com/docs/guides/vision/is-there-a-limit-to-the-size-of-the-image-i-can-upload
    3. PNG (.png), JPEG (.jpeg and .jpg), WEBP (.webp), and non-animated GIF (.gif) are only supported: https://platform.openai.com/docs/guides/vision/what-type-of-files-can-i-upload
    """
    client: OpenAI = create_openai_client()
    content_parts: list[ChatCompletionContentPartParam] = [
        {"type": "text", "text": DESCRIBE_IMAGE}
    ]
    if context is not None:
        logger.info("describe_image: appending context (%d chars)", len(context))
        content_parts.append({"type": "text", "text": context})
    content_parts.append(
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
                "detail": "auto",
            },
        }
    )
    messages: list[ChatCompletionMessageParam] = [
        {"role": "user", "content": content_parts}
    ]

    start = time.time()
    completion: ChatCompletion = client.chat.completions.create(
        messages=messages,
        model=OPENAI_MODEL_ID,
        n=1,
        # temperature=OPENAI_TEMPERATURE,
    )
    response_time_ms = int((time.time() - start) * 1000)
    message_content = completion.choices[0].message.content
    content: str | None = message_content.strip() if message_content else None
    description: str = content if content else "No response from OpenAI"
    usage = completion.usage
    insert_llm_request(
        usage_id=usage_id,
        provider="openai",
        model_id=OPENAI_MODEL_ID,
        input_messages=messages,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_message={"role": "assistant", "content": description},
        output_tokens=usage.completion_tokens if usage else 0,
        response_time_ms=response_time_ms,
        created_by=created_by,
    )
    logger.info("describe_image: returning description (%d chars)", len(description))
    return description
