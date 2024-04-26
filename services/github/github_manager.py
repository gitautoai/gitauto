# Standard imports
import base64
import datetime
import hashlib  # For HMAC (Hash-based Message Authentication Code) signatures
import hmac  # For HMAC (Hash-based Message Authentication Code) signatures
import logging
import time
from typing import Any

# Third-party imports
import jwt  # For generating JWTs (JSON Web Tokens)
import requests
from fastapi import Request

# Local imports
from config import (
    GITHUB_API_URL,
    GITHUB_API_VERSION,
    GH_APP_ID,
    GH_PRIVATE_KEY,
    TIMEOUT_IN_SECONDS,
    PRODUCT_ID,
)
from services.github.github_types import GitHubContentInfo, GitHubLabeledPayload
from services.supabase import SupabaseManager

from utils.file_manager import apply_patch
from utils.text_copy import request_issue_comment, request_limit_reached

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


def add_reaction_to_issue(
    owner: str, repo: str, issue_number: int, content: str, token: str
) -> None:
    """https://docs.github.com/en/rest/reactions/reactions?apiVersion=2022-11-28#create-reaction-for-an-issue"""
    try:
        response: requests.Response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/reactions",
            headers=create_headers(token=token),
            json={"content": content},
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()
        response.json()

    except requests.exceptions.HTTPError as e:
        logging.error(
            msg=f"add_reaction_to_issue HTTP Error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logging.error(msg=f"add_reaction_to_issue Error: {e}")


def commit_changes_to_remote_branch(
    branch: str,
    commit_message: str,
    diff_text: str,
    file_path: str,
    owner: str,
    repo: str,
    comment_url: str,
    unique_issue_id: str,
    token: str,
) -> None:
    """https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents"""
    url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}"
    try:
        # Get the SHA of the file if it exists
        get_response = requests.get(
            url=url, headers=create_headers(token=token), timeout=TIMEOUT_IN_SECONDS
        )
        original_text = ""
        sha = ""
        print(f"{get_response.status_code=}\n")
        if get_response.status_code == 200:
            get_json: GitHubContentInfo = get_response.json()
            original_text: str = base64.b64decode(s=get_json["content"]).decode(
                encoding="utf-8"
            )
            sha: str = get_json["sha"]
        elif get_response.status_code != 404:  # Error other than 'file not found'
            get_response.raise_for_status()

        # Create a new commit
        modified_text: str = apply_patch(
            original_text=original_text, diff_text=diff_text
        )
        if modified_text == "":
            return
        data: dict[str, str | None] = {
            "message": commit_message,
            "content": base64.b64encode(
                s=modified_text.encode(encoding="utf-8")
            ).decode(encoding="utf-8"),
            "branch": branch,
        }
        if sha != "":
            data["sha"] = sha
        put_response = requests.put(
            url=url,
            json=data,
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS,
        )
        put_response.raise_for_status()
    except Exception as e:
        # Do not raise/comment an error, we want to finish the PR even if there is a commit that fails
        logging.error(msg=f"commit_changes_to_remote_branch Error: {e}")


def create_comment(
    owner: str, repo: str, issue_number: int, body: str, token: str
) -> str:
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment"""
    try:
        response: requests.Response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=create_headers(token=token),
            json={
                "body": body,
            },
            timeout=TIMEOUT_IN_SECONDS,
        )

        response.raise_for_status()
        return response.json()["url"]
    # If this doesn't work, it means GitHub APIs are likely down, so we should raise
    except requests.exceptions.HTTPError as e:
        logging.error(
            msg=f"create_comment HTTP Error: {e.response.status_code} - {e.response.text}"
        )
        raise
    except Exception as e:
        logging.error(msg=f"create_comment Error: {e}")
        raise


def create_comment_on_issue_with_gitauto_button(payload: GitHubLabeledPayload) -> None:
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment"""
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)

    owner: str = payload["repository"]["owner"]["login"]
    owner_id: int = payload["repository"]["owner"]["id"]
    repo_name: str = payload["repository"]["name"]
    issue_number: int = payload["issue"]["number"]
    user_id: int = payload["sender"]["id"]
    user_name: str = payload["sender"]["login"]

    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # Proper issue generation comment, create user if not exist (first issue in an orgnanization)
    first_issue = False
    if not supabase_manager.user_exists(
        user_id=user_id, installation_id=installation_id
    ):
        supabase_manager.create_user(
            user_id=user_id,
            user_name=user_name,
            installation_id=installation_id,
        )
        first_issue = True
    elif supabase_manager.is_users_first_issue(
        user_id=user_id, installation_id=installation_id
    ):
        first_issue = True

    requests_left, request_count, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=user_id,
            installation_id=installation_id,
            user_name=user_name,
            owner_id=owner_id,
            owner_name=owner,
        )
    )

    body = "Click the checkbox below to generate a PR!\n- [ ] Generate PR"
    if PRODUCT_ID != "gitauto":
        body += " - " + PRODUCT_ID

    if end_date != datetime.datetime(
        year=1, month=1, day=1, hour=0, minute=0, second=0
    ):
        body += request_issue_comment(requests_left=requests_left, end_date=end_date)

    if requests_left <= 0:
        body = request_limit_reached(
            user_name=user_name,
            request_count=request_count,
            end_date=end_date,
        )

    if first_issue:
        body = "Welcome to GitAuto! 🎉\n" + body
        supabase_manager.set_user_first_issue_to_false(
            user_id=user_id, installation_id=installation_id
        )

    try:
        response: requests.Response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/issues/{issue_number}/comments",
            headers=create_headers(token=token),
            json={
                "body": body,
            },
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()

        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(
            msg=f"create_comment HTTP Error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logging.error(msg=f"create_comment Error: {e}")


def create_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def create_jwt() -> str:
    """Generate a JWT (JSON Web Token) for GitHub App authentication"""
    now = int(time.time())
    payload: dict[str, int | str] = {
        "iat": now,  # Issued at time
        "exp": now + 600,  # JWT expires in 10 minutes
        "iss": GH_APP_ID,  # Issuer
    }
    # The reason we use RS256 is that GitHub requires it for JWTs
    return jwt.encode(payload=payload, key=GH_PRIVATE_KEY, algorithm="RS256")


def create_pull_request(
    base: str,  # The branch name you want to merge your changes into. ex) 'main'
    body: str,
    head: str,  # The branch name that contains your changes
    owner: str,
    repo: str,
    title: str,
    comment_url: str,
    unique_issue_id: str,
    token: str,
) -> str:
    """https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request"""
    try:
        response: requests.Response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
            headers=create_headers(token=token),
            json={"title": title, "body": body, "head": head, "base": base},
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()
        return response.json()["html_url"]
    except Exception as e:
        update_comment_for_raised_errors(
            error=e,
            comment_url=comment_url,
            unique_issue_id=unique_issue_id,
            token=token,
            which_function=create_pull_request.__name__,
        )


def create_remote_branch(
    branch_name: str,
    owner: str,
    repo: str,
    sha: str,
    comment_url: str,
    unique_issue_id: str,
    token: str,
) -> None:
    try:
        response: requests.Response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs",
            headers=create_headers(token=token),
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()
    except Exception as e:
        update_comment_for_raised_errors(
            error=e,
            comment_url=comment_url,
            unique_issue_id=unique_issue_id,
            token=token,
            which_function=create_remote_branch.__name__,
        )


def get_installation_access_token(installation_id: int) -> str:
    """Get an access token for the installed GitHub App"""
    jwt_token: str = create_jwt()
    headers: dict[str, str] = create_headers(token=jwt_token)
    url: str = (
        f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    )

    try:
        response: requests.Response = requests.post(
            url=url, headers=headers, timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        return response.json()["token"]
    except requests.exceptions.HTTPError as e:
        logging.error(
            msg=f"get_installation_access_token HTTP Error: {e.response.status_code} - {e.response.text}"
        )
        raise
    except Exception as e:
        logging.error(msg=f"get_installation_access_token Error: {e}")
        raise


def get_issue_comments(
    owner: str, repo: str, issue_number: int, token: str
) -> list[str]:
    """https://docs.github.com/en/rest/issues/comments#list-issue-comments"""
    try:
        response = requests.get(
            url=f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()
        comments = response.json()
        comment_texts: list[str] = [comment["body"] for comment in comments]
        return comment_texts
    except requests.exceptions.HTTPError as e:
        logging.error(
            msg=f"get_issue_comments HTTP Error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logging.error(msg=f"get_issue_comments Error: {e}")


def get_latest_remote_commit_sha(
    owner: str,
    repo: str,
    branch: str,
    comment_url: str,
    unique_issue_id: str,
    token: str,
) -> str:
    """SHA stands for Secure Hash Algorithm. It's a unique identifier for a commit.
    https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#get-a-reference"""
    try:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()
        return response.json()["object"]["sha"]
    except Exception as e:
        update_comment_for_raised_errors(
            error=e,
            comment_url=comment_url,
            unique_issue_id=unique_issue_id,
            token=token,
            which_function=get_latest_remote_commit_sha.__name__,
        )


def get_remote_file_content(
    file_path: str,  # Ex) 'src/main.py'
    owner: str,
    ref: str,  # Ex) 'main'
    repo: str,
    token: str,
) -> str:
    """@link https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28"""
    url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers: dict[str, str] = create_headers(token=token)

    try:
        response: requests.Response = requests.get(
            url=url, headers=headers, timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        encoded_content: str = response.json()["content"]
        decoded_content: str = base64.b64decode(s=encoded_content).decode(
            encoding="utf-8"
        )
        # print(f"```{file_path}:\n{decoded_content}```")
        return decoded_content
    except requests.exceptions.HTTPError as e:
        logging.error(
            msg=f"get_remote_file_content HTTP Error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        # TODO in future ask GPT to try again
        logging.error(msg=f"get_remote_file_content Error: {e}")


def get_remote_file_tree(
    owner: str, repo: str, ref: str, comment_url: str, unique_issue_id: str, token: str
) -> list[str]:
    """Get the file tree of a GitHub repository."""
    try:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1",
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()
        return [item["path"] for item in response.json()["tree"]]
    except Exception as e:
        update_comment_for_raised_errors(
            error=e,
            comment_url=comment_url,
            unique_issue_id=unique_issue_id,
            token=token,
            which_function=get_remote_file_tree.__name__,
        )


async def verify_webhook_signature(request: Request, secret: str) -> None:
    """Verify the webhook signature for security"""
    signature: str | None = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        raise ValueError("Missing webhook signature")
    body: bytes = await request.body()

    # Compare the computed signature with the one in the headers
    hmac_key: bytes = secret.encode()
    hmac_signature: str = hmac.new(
        key=hmac_key, msg=body, digestmod=hashlib.sha256
    ).hexdigest()
    expected_signature: str = "sha256=" + hmac_signature
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid webhook signature")


def update_comment(comment_url: str, body: str, token: str) -> dict[str, Any]:
    """https://docs.github.com/en/rest/issues/comments#update-an-issue-comment"""
    try:
        response: requests.Response = requests.patch(
            url=comment_url,
            headers=create_headers(token=token),
            json={
                "body": body,
            },
            timeout=TIMEOUT_IN_SECONDS,
        )
        response.raise_for_status()

        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(
            msg=f"update_comment HTTP Error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logging.error(msg=f"update_comment Error: {e}")


def update_comment_for_raised_errors(
    error: Any, comment_url: str, unique_issue_id: str, token: str, which_function: str
) -> dict[str, Any]:
    """Update the comment on issue with an error message and raise the error."""
    body = "Sorry, we have an error. Please try again."
    try:
        if isinstance(error, requests.exceptions.HTTPError):
            logging.error(
                "%s HTTP Error: %s - %s",
                which_function,
                error.response.status_code,
                error.response.text,
            )
            if (
                error.response.status_code == 422
                and error["message"]
                and error.message == "Validation Failed"
                and (
                    (
                        isinstance(error.errors[0], list)
                        and hasattr(error.errors[0][0], "message")
                        and error.errors[0][0].message.find(
                            "No commits between main and"
                        )
                        != -1
                    )
                    or (
                        not isinstance(error.errors[0], list)
                        and hasattr(error.errors[0], "message")
                        and error.errors[0].message.find("No commits between main and")
                        != -1
                    )
                )
            ):
                body = (
                    "No changes were detected. Please add more details to the issue and try again.",
                )
            else:
                logging.error(
                    "%s HTTP Error: %s - %s",
                    which_function,
                    error.response.status_code,
                    error.response.text,
                )
        else:
            logging.error("%s Error: %s", which_function, error)
    except Exception as e:
        logging.error("%s Error: %s", which_function, e)
    update_comment(comment_url=comment_url, token=token, body=body)

    raise RuntimeError("Error occurred")
