import logging

# Third-party imports
from openai.pagination import SyncCursorPage
from openai.types.beta.threads import ThreadMessage


# Pretty printing helper
def pretty_print(messages: SyncCursorPage[ThreadMessage]) -> None:
    logging.info("# Messages")
    for m in messages:
        logging.info(f"{m.role}: {m.content[0].text.value}")
    logging.info()
