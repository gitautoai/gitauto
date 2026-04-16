# Standard imports
import json

# Third-party imports
from anthropic.types import MessageParam
from google.genai import types

# Local imports
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def convert_messages_to_google(messages: list[MessageParam]):
    """Convert Anthropic-format messages to Google AI Content objects.
    chat_with_agent builds all messages in Anthropic format regardless of provider.
    Anthropic tool_use (id, name, input) -> Google FunctionCall (name, args).
    Anthropic tool_result -> Google FunctionResponse."""
    contents: list[types.Content] = []

    for msg in messages:
        role = msg["role"]
        raw_content = msg["content"]

        # Google uses "user" and "model" roles
        google_role = "model" if role == "assistant" else "user"
        parts: list[types.Part] = []

        if isinstance(raw_content, str):
            parts.append(types.Part(text=raw_content))
        elif isinstance(raw_content, list):
            for block in raw_content:
                if not isinstance(block, dict):
                    continue

                # Discriminated union: block["type"] narrows to the specific TypedDict
                if block["type"] == "text":
                    parts.append(types.Part(text=block["text"]))

                elif block["type"] == "tool_use":
                    # Anthropic tool_use -> Google FunctionCall
                    args = block["input"]
                    if not isinstance(args, dict):
                        args = {}
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
                    # Anthropic tool_result -> Google FunctionResponse
                    content_val = block.get("content")
                    if isinstance(content_val, list):
                        content_val = json.dumps(content_val)
                    elif not isinstance(content_val, str):
                        content_val = ""
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=block["tool_use_id"],
                                response={"result": content_val},
                                id=block["tool_use_id"],
                            )
                        )
                    )

        if parts:
            contents.append(types.Content(role=google_role, parts=parts))

    return contents
