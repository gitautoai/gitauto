from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def sanitize_tool_args(tool_args: dict[str, object]):
    for key, val in tool_args.items():
        if isinstance(val, str) and "</antml" in val:
            cleaned = val.split("</antml")[0].strip()
            logger.warning(
                "Stripped malformed XML from tool_args[%s]: %r -> %r",
                key,
                val,
                cleaned,
            )
            tool_args[key] = cleaned
