from constants.claude import ClaudeModelId
from services.claude.client import claude
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="", raise_on_error=False)
def chat_with_claude_simple(
    system_input: str,
    user_input: str,
    model_id: ClaudeModelId = ClaudeModelId.SONNET_4_6,
):
    response = claude.messages.create(
        model=model_id,
        system=system_input,
        messages=[{"role": "user", "content": user_input}],
        max_tokens=4096,
        temperature=0.0,
    )
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text
    if not text:
        logger.warning("Claude returned empty text response")
    return text
