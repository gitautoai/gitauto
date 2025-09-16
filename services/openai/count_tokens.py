# Third-party imports
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
import tiktoken

# Local imports
from config import OPENAI_MODEL_ID_FOR_TIKTOKEN
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=0, raise_on_error=False)
def count_tokens(messages: list[ChatCompletionMessageParam]) -> int:
    encoding: tiktoken.Encoding = tiktoken.encoding_for_model(
        model_name=OPENAI_MODEL_ID_FOR_TIKTOKEN
    )
    num_tokens = 0
    for message in messages:
        if "role" in message:
            num_tokens += len(encoding.encode(message["role"]))
        if "content" in message:
            content = message["content"]
            if isinstance(content, str):
                num_tokens += len(encoding.encode(content or ""))
            elif isinstance(content, list):
                for block in content:
                    if block.get("type") == "text":
                        num_tokens += len(encoding.encode(block.get("text", "")))
                    elif block.get("type") == "tool_use":
                        num_tokens += len(encoding.encode(block.get("name", "")))
                        num_tokens += len(encoding.encode(str(block.get("input", ""))))
                    elif block.get("type") == "tool_result":
                        num_tokens += len(
                            encoding.encode(str(block.get("content", "")))
                        )
        if "name" in message:
            num_tokens += len(encoding.encode(message["name"]))
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                if "function" in tool_call:
                    function = tool_call["function"]
                    num_tokens += len(encoding.encode(function["name"]))
                    num_tokens += len(encoding.encode(function["arguments"]))

    return num_tokens
