# Third party imports
from anthropic.types import MessageParam

# Local imports
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=0, raise_on_error=False)
def measure_messages_chars(messages: list[MessageParam]):
    total = 0
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            total += len(content)
            continue
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            total += sum(len(v) for v in block.values() if isinstance(v, str))
    return total
