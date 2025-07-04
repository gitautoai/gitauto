from config import GITHUB_APP_USER_NAME
from services.github.comments.get_all_comments import get_all_comments
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def has_comment_with_text(base_args: BaseArgs, texts: list[str]):
    comments = get_all_comments(base_args)

    for comment in comments:
        if comment.get("user", {}).get("login") != GITHUB_APP_USER_NAME:
            continue

        comment_body = comment.get("body", "")
        for text in texts:
            if text in comment_body:
                return True

    return False
