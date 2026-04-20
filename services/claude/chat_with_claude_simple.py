import time

from constants.models import ClaudeModelId
from services.claude.client import claude
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="", raise_on_error=False)
def chat_with_claude_simple(
    system_input: str,
    user_input: str,
    usage_id: int,
    model_id: ClaudeModelId = ClaudeModelId.SONNET_4_6,
):
    start = time.time()
    # Opus 4.7 deprecated the temperature parameter; omit it to stay compatible across models.
    response = claude.messages.create(
        model=model_id,
        system=system_input,
        messages=[{"role": "user", "content": user_input}],
        max_tokens=4096,
    )
    response_time_ms = int((time.time() - start) * 1000)

    text = ""
    for block in response.content:
        if block.type == "text":
            logger.info("chat_with_claude_simple: text block appended")
            text += block.text
    if not text:
        logger.warning("Claude returned empty text response")

    input_tokens = response.usage.input_tokens if response.usage else 0
    output_tokens = response.usage.output_tokens if response.usage else 0
    insert_llm_request(
        usage_id=usage_id,
        provider="claude",
        model_id=model_id,
        input_messages=[{"role": "user", "content": user_input}],
        input_tokens=input_tokens,
        output_message={"role": "assistant", "content": text},
        output_tokens=output_tokens,
        response_time_ms=response_time_ms,
        created_by="chat_with_claude_simple",
    )

    logger.info("chat_with_claude_simple returning text of length %d", len(text))
    return text
