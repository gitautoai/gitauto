import tiktoken
from config import (
    OPENAI_MAX_CONTEXT_TOKENS,
    OPENAI_MODEL_ID_FOR_TIKTOKEN,
    OPENAI_MAX_STRING_LENGTH,
)
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def truncate_message(input_message: str) -> str:
    # First truncate by string length if needed
    truncated_message: str = input_message[:OPENAI_MAX_STRING_LENGTH]

    # Then handle token truncation
    encoding: tiktoken.Encoding = tiktoken.encoding_for_model(
        model_name=OPENAI_MODEL_ID_FOR_TIKTOKEN
    )
    tokens: list[int] = encoding.encode(text=truncated_message)
    if len(tokens) > OPENAI_MAX_CONTEXT_TOKENS:
        tokens = tokens[:OPENAI_MAX_CONTEXT_TOKENS]
        truncated_message: str = encoding.decode(tokens=tokens)
    return truncated_message
