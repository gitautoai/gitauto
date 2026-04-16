from anthropic.types import MessageParam, ToolUnionParam

from constants.models import ClaudeModelId, GoogleModelId, ModelId
from services.claude.chat_with_claude import chat_with_claude
from services.google_ai.chat_with_google import chat_with_google
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
def chat_with_model(
    messages: list[MessageParam],
    system_content: str,
    tools: list[ToolUnionParam],
    model_id: ModelId,
    usage_id: int,
    created_by: str,
):
    if isinstance(model_id, ClaudeModelId):
        logger.info("Routing to Claude: %s", model_id)
        return chat_with_claude(
            messages=messages,
            system_content=system_content,
            tools=tools,
            model_id=model_id,
            usage_id=usage_id,
            created_by=created_by,
        )

    if isinstance(model_id, GoogleModelId):
        logger.info("Routing to Google AI: %s", model_id)
        return chat_with_google(
            messages=messages,
            system_content=system_content,
            tools=tools,
            model_id=model_id,
            usage_id=usage_id,
            created_by=created_by,
        )

    raise ValueError(f"Unknown provider for model '{model_id}'")
