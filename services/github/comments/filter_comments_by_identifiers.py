from config import GITHUB_APP_USER_NAME
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_comments_by_identifiers(comments: list[dict], identifiers: list[str]):
    """Filter comments by identifier text(s) and made by GitAuto"""
    comments = comments or []

    return [
        comment
        for comment in comments
        if any(identifier in comment["body"] for identifier in identifiers)
        and comment["user"]["login"] == GITHUB_APP_USER_NAME
    ]
