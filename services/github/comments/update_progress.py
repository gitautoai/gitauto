from services.github.comments.update_comment import update_comment
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.add_log_message import add_log_message
from utils.progress_bar.progress_bar import create_progress_bar


@handle_exceptions(default_return_value=0, raise_on_error=False)
def update_progress(
    msg: str,
    p: int,
    log_messages: list[str],
    base_args: BaseArgs,
):
    """Increment progress by 5, log a message, and update the GitHub comment."""
    p += 5
    add_log_message(msg, log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)
    return p
