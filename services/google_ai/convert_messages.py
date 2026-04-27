# Standard imports
import json

# Third-party imports
from anthropic.types import MessageParam
from google.genai import types

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def convert_messages_to_google(messages: list[MessageParam]):
    """Convert Anthropic-format messages to Google AI Content objects.
    chat_with_agent builds all messages in Anthropic format regardless of provider.
    Anthropic tool_use (id, name, input) -> Google FunctionCall (name, args).
    Anthropic tool_result -> Google FunctionResponse.

    Consecutive same-role messages get merged into a single Content. Anthropic accepts multiple consecutive user-role messages (chat_with_agent emits two on first turn: one with the JSON task payload, one with the source code), but Google's API requires strict user/model alternation and rejects same-role consecutive Contents with a generic 400 INVALID_ARGUMENT (Sentry AGENT-36R/36K/36N/36P, gitautoai/website 2026-04-16). Merging keeps every part in order without changing semantics.
    """
    contents: list[types.Content] = []

    # Map tool_use_id -> function name for FunctionResponse.name (must match FunctionDeclaration.name)
    tool_id_to_name: dict[str, str] = {}

    for msg in messages:
        role = msg["role"]
        raw_content = msg["content"]

        # Google uses "user" and "model" roles
        google_role = "model" if role == "assistant" else "user"
        parts: list[types.Part] = []

        if isinstance(raw_content, str):
            logger.info("convert_messages_to_google: appending plain-text part")
            parts.append(types.Part(text=raw_content))
        elif isinstance(raw_content, list):
            logger.info(
                "convert_messages_to_google: walking %d content blocks",
                len(raw_content),
            )
            for block in raw_content:
                if not isinstance(block, dict):
                    logger.info("convert_messages_to_google: non-dict block, skipping")
                    continue

                # Discriminated union: block["type"] narrows to the specific TypedDict
                if block["type"] == "text":
                    logger.info("convert_messages_to_google: appending text block")
                    parts.append(types.Part(text=block["text"]))

                elif block["type"] == "tool_use":
                    logger.info(
                        "convert_messages_to_google: converting tool_use to FunctionCall"
                    )
                    args = block["input"]
                    if not isinstance(args, dict):
                        logger.info(
                            "convert_messages_to_google: tool_use input is not dict, defaulting to {}"
                        )
                        args = {}
                    tool_id_to_name[block["id"]] = block["name"]
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=block["name"],
                                args=args,
                                id=block["id"],
                            )
                        )
                    )

                elif block["type"] == "tool_result":
                    logger.info(
                        "convert_messages_to_google: converting tool_result to FunctionResponse"
                    )
                    content_val = block.get("content")
                    if isinstance(content_val, list):
                        logger.info(
                            "convert_messages_to_google: tool_result content is list, json-dumping"
                        )
                        content_val = json.dumps(content_val)
                    elif not isinstance(content_val, str):
                        logger.info(
                            "convert_messages_to_google: tool_result content is non-string non-list, defaulting to ''"
                        )
                        content_val = ""
                    tool_use_id = block["tool_use_id"]
                    func_name = tool_id_to_name.get(tool_use_id, tool_use_id)
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=func_name,
                                response={"result": content_val},
                                id=tool_use_id,
                            )
                        )
                    )

        if not parts:
            logger.info(
                "convert_messages_to_google: empty parts list, skipping message"
            )
            continue

        # Merge into the previous Content if the role matches, otherwise append.
        if contents and contents[-1].role == google_role:
            logger.info(
                "convert_messages_to_google: merging %d parts into previous %s Content",
                len(parts),
                google_role,
            )
            existing_parts = list(contents[-1].parts or [])
            existing_parts.extend(parts)
            contents[-1] = types.Content(role=google_role, parts=existing_parts)
        else:
            logger.info(
                "convert_messages_to_google: appending new %s Content (%d parts)",
                google_role,
                len(parts),
            )
            contents.append(types.Content(role=google_role, parts=parts))

    logger.info("convert_messages_to_google: returning %d Contents", len(contents))
    return contents
