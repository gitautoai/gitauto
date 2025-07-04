from config import GITHUB_APP_USER_NAME
from constants.messages import PERMISSION_DENIED_MESSAGE
from services.github.comments.get_all_comments import get_all_comments
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def has_permission_comment(base_args: BaseArgs) -> bool:
    comments = get_all_comments(base_args)

    for comment in comments:
        if comment.get("user", {}).get(
            "login"
        ) == GITHUB_APP_USER_NAME and PERMISSION_DENIED_MESSAGE in comment.get(
            "body", ""
        ):
            return True

    return False
