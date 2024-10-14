# Third-party imports
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
import tiktoken

# Local imports
from config import OPENAI_MODEL_ID_GPT_4O
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=0, raise_on_error=False)
def count_tokens(messages: list[ChatCompletionMessageParam]) -> int:
    encoding: tiktoken.Encoding = tiktoken.encoding_for_model(
        model_name=OPENAI_MODEL_ID_GPT_4O
    )
    num_tokens = 0
    for message in messages:
        if "role" in message:
            num_tokens += len(encoding.encode(message["role"]))
        if "content" in message:
            num_tokens += len(encoding.encode(message["content"] or ""))
        if "name" in message:
            num_tokens += len(encoding.encode(message["name"]))
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                if "function" in tool_call:
                    function = tool_call["function"]
                    num_tokens += len(encoding.encode(function["name"]))
                    num_tokens += len(encoding.encode(function["arguments"]))

    return num_tokens
