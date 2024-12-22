from requests import delete, get
from config import GITHUB_API_URL, TIMEOUT
from constants.messages import CLICK_THE_CHECKBOX
from services.github.create_headers import create_headers
from services.github.github_types import BaseArgs
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def post_comment(base_args: BaseArgs, issue_id: int, message: str):
    """Post a comment on a GitHub issue"""
    owner, repo, token = (base_args["owner"], base_args["repo"], base_args["token"])
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_id}/comments"
    headers: dict[str, str] = create_headers(token=token)
    data = {"body": message}
    response = post(url=url, headers=headers, json=data, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_a_comment(base_args: BaseArgs, comment_id: str):
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#delete-an-issue-comment"""
    owner, repo, token = (base_args["owner"], base_args["repo"], base_args["token"])
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/comments/{comment_id}"
    headers: dict[str, str] = create_headers(token=token)
    response = delete(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_all_comments(base_args: BaseArgs):
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments"""
    owner, repo, issue_number, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["issue_number"],
        base_args["token"],
    )
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers: dict[str, str] = create_headers(token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    comments: list[dict] = response.json()
    # print(f"All comments: {dumps(obj=comments, indent=2)}")
    return comments


def filter_my_comments(comments: list[dict]):
    """Filter out comments made by GitAuto except the one with the checkbox"""
    return [
        comment for comment in comments if CLICK_THE_CHECKBOX not in comment["body"]
    ]


def delete_my_comments(base_args: BaseArgs):
    """Delete all comments made by GitAuto except the one with the checkbox"""
    comments = get_all_comments(base_args)
    my_comments = filter_my_comments(comments)
    # print(f"My comments: {dumps(obj=my_comments, indent=2)}")
    for comment in my_comments:
        delete_a_comment(base_args=base_args, comment_id=comment["id"])
