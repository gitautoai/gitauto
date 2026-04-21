# Standard imports
import time
import uuid

# Third-party imports
from anthropic.types import MessageParam, ToolUnionParam
from google.genai import types

# Local imports
from constants.models import GoogleModelId
from services.google_ai.client import get_google_ai_client
from services.google_ai.convert_messages import convert_messages_to_google
from services.google_ai.convert_tools import convert_tools_to_google
from services.llm_result import LlmResult, ToolCall
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
def chat_with_google(
    messages: list[MessageParam],
    system_content: str,
    tools: list[ToolUnionParam],
    model_id: GoogleModelId,
    usage_id: int,
    created_by: str,
):
    # Convert Anthropic-format messages and tools to Google format
    google_contents = convert_messages_to_google(messages)
    google_tools = convert_tools_to_google(tools)

    config = types.GenerateContentConfig(
        system_instruction=system_content,
        tools=google_tools,
        temperature=0.0,
        # chat_with_agent manages the tool-call loop, so disable the SDK's auto-execution
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    client = get_google_ai_client()
    start_time = time.time()
    response = client.models.generate_content(
        model=model_id,
        contents=google_contents,
        config=config,
    )
    response_time_ms = int((time.time() - start_time) * 1000)

    # Extract token counts
    usage = response.usage_metadata
    token_input = (usage.prompt_token_count or 0) if usage else 0
    token_output = (usage.candidates_token_count or 0) if usage else 0

    # Process response: extract text and function calls
    content_text = ""
    tool_calls: list[ToolCall] = []
    content_list = []

    if response.candidates:
        logger.info(
            "chat_with_google: response has %d candidate(s); parsing first",
            len(response.candidates),
        )
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            logger.info(
                "chat_with_google: candidate has %d part(s); iterating",
                len(candidate.content.parts),
            )
            for part in candidate.content.parts:
                if part.text:
                    logger.info(
                        "chat_with_google: part is text (%d chars); appending to content_text",
                        len(part.text),
                    )
                    content_text += part.text
                elif part.function_call:
                    logger.info(
                        "chat_with_google: part is function_call=%s; building ToolCall",
                        part.function_call.name,
                    )
                    fc = part.function_call
                    # Generate a tool_use ID matching Anthropic format
                    tool_id = fc.id or f"toolu_{uuid.uuid4().hex[:24]}"
                    tool_calls.append(
                        ToolCall(
                            id=tool_id,
                            name=fc.name or "",
                            args=dict(fc.args) if fc.args else None,
                        )
                    )

    # Build content list in Anthropic format
    if content_text:
        logger.info(
            "chat_with_google: assembling content_list with text block (%d chars)",
            len(content_text),
        )
        content_list.append({"type": "text", "text": content_text})

    for tc in tool_calls:
        content_list.append(
            {
                "type": "tool_use",
                "id": tc.id,
                "name": tc.name,
                "input": tc.args or {},
            }
        )

    # Return in Anthropic MessageParam format for compatibility
    assistant_message: MessageParam = {
        "role": "assistant",
        "content": content_list if content_list else content_text,
    }

    # Log to Supabase
    system_msg: MessageParam = {"role": "user", "content": system_content}
    full_messages = [system_msg, *messages]
    llm_record = insert_llm_request(
        usage_id=usage_id,
        provider="google",
        model_id=model_id,
        input_messages=full_messages,
        input_tokens=token_input,
        output_message=assistant_message,
        output_tokens=token_output,
        response_time_ms=response_time_ms,
        created_by=created_by,
    )
    cost_usd = llm_record["total_cost_usd"] if llm_record else 0.0

    logger.info(
        "Google AI response: model=%s, input_tokens=%d, output_tokens=%d, tool_calls=%d",
        model_id,
        token_input,
        token_output,
        len(tool_calls),
    )

    return LlmResult(
        assistant_message=assistant_message,
        tool_calls=tool_calls,
        token_input=token_input,
        token_output=token_output,
        cost_usd=cost_usd,
    )
