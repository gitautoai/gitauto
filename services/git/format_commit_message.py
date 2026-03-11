# Local imports
from config import GITHUB_APP_USER_ID
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def format_commit_message(message: str, base_args: BaseArgs):
    """Append Co-Authored-By trailer so the sender gets GitHub contribution credit."""
    sender_id = base_args["sender_id"]

    # When sender is GitAuto (e.g. schedule handler), credit all human reviewers
    if sender_id == GITHUB_APP_USER_ID:
        human_reviewers = [
            r for r in base_args.get("reviewers", []) if "[bot]" not in r
        ]
        if not human_reviewers:
            return message
        trailers = "\n".join(
            f"Co-Authored-By: {r} <{r}@users.noreply.github.com>"
            for r in human_reviewers
        )
        return f"{message}\n\n{trailers}"

    sender_display_name = base_args["sender_display_name"]
    sender_email = base_args["sender_email"]
    sender_name = base_args["sender_name"]

    if sender_email is None:
        sender_email = f"{sender_id}+{sender_name}@users.noreply.github.com"

    return f"{message}\n\nCo-Authored-By: {sender_display_name} <{sender_email}>"
