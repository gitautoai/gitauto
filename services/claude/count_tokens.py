from anthropic import Anthropic
from anthropic.types import MessageParam

from constants.models import ClaudeModelId
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=0, raise_on_error=False)
def count_tokens_claude(
    messages: list[MessageParam],
    client: Anthropic,
    model: ClaudeModelId,
):
    """Return the Anthropic-side input_tokens for the given messages and model."""
    result = client.messages.count_tokens(messages=messages, model=model)
    logger.info("count_tokens_claude: input_tokens=%d", result.input_tokens)
    return result.input_tokens
