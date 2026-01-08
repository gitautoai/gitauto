import logging

from requests import patch

from config import TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_comment(body: str, base_args: BaseArgs):
    """https://docs.github.com/en/rest/issues/comments#update-an-issue-comment"""
    token = base_args["token"]
    comment_url = base_args.get("comment_url")
    if comment_url is None:
        return None

    print(body + "\n")
    response = patch(
        url=comment_url,
        headers=create_headers(token=token),
        json={"body": body},
        timeout=TIMEOUT,
    )

    # Handle 404 (Client Error: Not Found for url) errors silently since they're expected when comments are deleted
    if response.status_code == 404:
        logging.info("Comment %s not found", comment_url)
        return None

    response.raise_for_status()
    return response.json()
