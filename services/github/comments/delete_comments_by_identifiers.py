from services.github.comments.delete_comment import delete_comment
from services.github.comments.filter_comments_by_identifiers import (
    filter_comments_by_identifiers,
)
from services.github.comments.get_all_comments import get_all_comments
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_comments_by_identifiers(
    *,
    owner: str,
    repo: str,
    issue_number: int,
    token: str,
    identifiers: list[str],
):
    """Delete all comments containing the identifiers made by GitAuto"""
    comments = get_all_comments(
        owner=owner, repo=repo, issue_number=issue_number, token=token
    )
    matching_comments = filter_comments_by_identifiers(comments, identifiers)
    for comment in matching_comments:
        delete_comment(owner=owner, repo=repo, token=token, comment_id=comment["id"])
