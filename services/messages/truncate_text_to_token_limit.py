from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="", raise_on_error=False)
def truncate_text_to_token_limit(
    text: str,
    current_tokens: int,
    max_tokens: int,
):
    """Proportionally truncate `text` to fit max_tokens, with a 0.9 safety margin for tokenizer-vs-character ratio jitter.

    Returns `text` unchanged when current_tokens <= max_tokens. Otherwise returns the leading slice plus an explicit truncation marker so downstream callers can see what happened.

    This is the single-message complement to trim_messages_to_token_limit: when a caller has only one message and the trim loop's "preserve first user message" rule would leave the payload untouched, we have to character-truncate the content itself.

    Real-world trigger: the `query_file` tool sends the full content of an arbitrary file as a single user message, so a giant CI log can blow past the model context. AGENT-36A/36B/36C: 205k-token PHPUnit dump from .gitauto/ci_error_log.txt produced an Anthropic 400 prompt-too-long until this helper landed.
    """
    if current_tokens <= max_tokens:
        logger.info(
            "truncate_text_to_token_limit: %d <= %d, no truncation",
            current_tokens,
            max_tokens,
        )
        return text

    keep_ratio = max_tokens / current_tokens
    new_len = int(len(text) * keep_ratio * 0.9)
    logger.warning(
        "truncate_text_to_token_limit: %d tokens > %d max; cutting %d chars to %d (keep_ratio=%.3f)",
        current_tokens,
        max_tokens,
        len(text),
        new_len,
        keep_ratio,
    )
    return (
        text[:new_len]
        + f"\n\n... [truncated at ~{max_tokens} tokens; original was {current_tokens}]"
    )
