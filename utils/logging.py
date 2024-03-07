# Third-party imports
from openai.pagination import SyncCursorPage
from openai.types.beta.threads import ThreadMessage


# Pretty printing helper
def pretty_print(messages: SyncCursorPage[ThreadMessage]) -> None:
    print("# Messages")
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")
    print()
