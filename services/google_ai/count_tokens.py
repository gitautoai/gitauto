from anthropic.types import MessageParam
from google.genai import Client

from constants.models import GoogleModelId
from services.google_ai.convert_messages import convert_messages_to_google
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=0, raise_on_error=False)
def count_tokens_google(
    messages: list[MessageParam],
    client: Client,
    model: GoogleModelId,
):
    """Return the Google-side total_tokens for the given messages and model.

    Messages are expected in Anthropic MessageParam format; they get converted
    to Google Content shape before counting since google-genai only tokenizes
    its own format."""
    contents = convert_messages_to_google(messages)
    result = client.models.count_tokens(model=model, contents=contents)
    logger.info("count_tokens_google: total_tokens=%s", result.total_tokens)
    return result.total_tokens or 0
