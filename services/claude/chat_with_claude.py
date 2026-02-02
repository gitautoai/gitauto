# Standard imports
import time

# Third party imports
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUnionParam, ToolUseBlock

# Local imports
from constants.claude import CLAUDE_MAX_TOKENS, CLAUDE_MODEL_ID_45
from services.claude.client import claude
from services.claude.exceptions import (
    ClaudeAuthenticationError,
    ClaudeOverloadedError,
)
from services.claude.remove_duplicate_get_remote_file_content_results import (
    remove_duplicate_get_remote_file_content_results,
)
from services.claude.remove_get_remote_file_content_before_replace_remote_file_content import (
    remove_get_remote_file_content_before_replace_remote_file_content,
)
from services.claude.remove_old_assistant_text import remove_old_assistant_text
from services.claude.remove_outdated_apply_diff_to_file_attempts_and_results import (
    remove_outdated_apply_diff_to_file_attempts_and_results,
)
from services.claude.trim_messages import trim_messages_to_token_limit
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_claude(
    messages: list[MessageParam],
    system_content: str,
    tools: list[ToolUnionParam],
    model_id: str = CLAUDE_MODEL_ID_45,
    usage_id: int | None = None,
):
    # https://docs.anthropic.com/en/api/client-sdks
    # Apply all message deduplication functions to save tokens
    messages = remove_duplicate_get_remote_file_content_results(messages)
    messages = remove_get_remote_file_content_before_replace_remote_file_content(
        messages
    )
    messages = remove_outdated_apply_diff_to_file_attempts_and_results(messages)
    messages = remove_old_assistant_text(messages)

    # Check token count and delete messages if necessary
    buffer = 4096
    max_input = 200_000 - CLAUDE_MAX_TOKENS - buffer
    messages, token_input = trim_messages_to_token_limit(
        messages=messages, client=claude, model=model_id, max_input=max_input
    )

    # https://docs.anthropic.com/en/api/messages
    start_time = time.time()
    try:
        response = claude.messages.create(
            model=model_id,
            system=system_content,
            messages=messages,
            tools=tools,
            # https://docs.anthropic.com/en/docs/about-claude/models/all-models#model-comparison-table
            max_tokens=CLAUDE_MAX_TOKENS,
            temperature=0.0,
        )
        response_time_ms = int((time.time() - start_time) * 1000)
    except OverloadedError as e:
        raise ClaudeOverloadedError("Claude API is overloaded (529)") from e
    except AuthenticationError as e:
        raise ClaudeAuthenticationError("Claude API authentication failed (401)") from e

    # Process the response
    tool_use_id = None
    tool_name = None
    tool_args = None
    content_text = ""

    # Check for tool calls in the response
    tool_use_blocks: list[ToolUseBlock] = []

    for content_block in response.content:
        if content_block.type == "text":
            content_text += content_block.text
        elif content_block.type == "tool_use":
            tool_use_blocks.append(content_block)

    # Build content list first, then create message
    content_list = []

    if content_text:  # Only add text block if there's content
        content_list.append({"type": "text", "text": content_text})

    if tool_use_blocks:
        # Process the first tool call
        tool_use = tool_use_blocks[0]
        tool_use_id = tool_use.id  # e.g. "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        tool_name = tool_use.name  # e.g. "apply_diff_to_file"
        tool_args = tool_use.input

        content_list.append(
            {
                "type": "tool_use",
                "id": tool_use_id,
                "name": tool_name,
                "input": tool_args,
            }
        )

    # Return Claude's native format
    assistant_message: MessageParam = {
        "role": "assistant",
        "content": content_list,
    }

    # Get actual output tokens from response
    token_output = (
        response.usage.output_tokens
        if hasattr(response, "usage") and response.usage
        else 0
    )

    # Combine system message with user messages for logging
    if usage_id is not None:
        system_msg: MessageParam = {"role": "user", "content": system_content}
        full_messages = [system_msg] + list(messages)
        insert_llm_request(
            usage_id=usage_id,
            provider="claude",
            model_id=model_id,
            input_messages=full_messages,
            input_tokens=token_input,
            output_message=assistant_message,
            output_tokens=token_output,
            response_time_ms=response_time_ms,
        )

    return (
        assistant_message,
        tool_use_id,
        tool_name,
        tool_args,
        token_input,
        token_output,
    )
