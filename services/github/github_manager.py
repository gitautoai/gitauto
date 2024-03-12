class GitHubManager:
    def __init__(self, token: str):
        self.token = token

    def commit_changes_to_remote_branch(self, branch: str, commit_message: str, diff_text: str, file_path: str, owner: str, repo: str) -> None:
        # Method implementation ...

    # Other methods ...


# Standard imports
import base64
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
    GITHUB_API_URL, GITHUB_API_VERSION, GITHUB_APP_ID, GITHUB_PRIVATE_KEY, TIMEOUT_IN_SECONDS
)
from services.github.github_types import GitHubContentInfo
from utils.file_manager import apply_patch


def commit_changes_to_remote_branch(
        branch: str,
        commit_message: str,
        diff_text: str,
        file_path: str,
        owner: str,
        repo: str,
        token: str
        ) -> None:
    """ https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents """
    url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}"
    try:
        # Get the SHA of the file if it exists
        get_response = requests.get(
            url=url,
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS
        )
        original_text = ""
        sha = ""
        print(f"{get_response.status_code=}\n")
        if get_response.status_code == 200:
            get_json: GitHubContentInfo = get_response.json()
            original_text: str = base64.b64decode(s=get_json['content']).decode(encoding='utf-8')
            sha: str = get_json['sha']
        elif get_response.status_code != 404:  # Error other than 'file not found'
            get_response.raise_for_status()

        # Create a new commit
        modified_text: str = apply_patch(original_text=original_text, diff_text=diff_text)
        data: dict[str, str | None] = {
            "message": commit_message,
            "content": base64.b64encode(s=modified_text.encode(encoding='utf-8'))
            .decode(encoding='utf-8'),
            "branch": branch,
        }
        if sha != "":
            data["sha"] = sha
        put_response = requests.put(
            url=url,
            json=data,
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS
        )
        put_response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


def create_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def create_jwt() -> str:
    """ Generate a JWT (JSON Web Token) for GitHub App authentication """
    now = int(time.time())
    payload: dict[str, int | str] = {
        "iat": now,  # Issued at time
        "exp": now + 600,  # JWT expires in 10 minutes
        "iss": GITHUB_APP_ID,  # Issuer
    }
    # The reason we use RS256 is that GitHub requires it for JWTs
    return jwt.encode(payload=payload, key=GITHUB_PRIVATE_KEY, algorithm="RS256")


def create_pull_request(
        base: str,  # The branch name you want to merge your changes into. ex) 'main'
        body: str,
        head: str,  # The branch name that contains your changes
        owner: str,
        repo: str,
        title: str,
        token: str
        ) -> dict[str, Any]:
    """ https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request """
    try:
        response: requests.Response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
            headers=create_headers(token=token),
            json={"title": title, "body": body, "head": head, "base": base},
            timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


def create_remote_branch(
        branch_name: str,
        owner: str,
        repo: str,
        sha: str,
        token: str
        ) -> None:
    try:
        response: requests.Response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs",
            headers=create_headers(token=token),
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
            timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


def get_installation_access_token(installation_id: int) -> str:
    """ Get an access token for the installed GitHub App """
    jwt_token: str = create_jwt()
    headers: dict[str, str] = create_headers(token=jwt_token)
    url: str = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    try:
        response: requests.Response = requests.post(
            url=url,
            headers=headers,
            timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        return response.json()["token"]
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


def get_issue_comments(owner: str, repo: str, issue_number: int, token: str) -> list[str]:
    """ https://docs.github.com/en/rest/issues/comments#list-issue-comments """
    try:
        response = requests.get(
            url=f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        comments = response.json()
        comment_texts: list[str] = [comment['body'] for comment in comments]
        return comment_texts
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


def get_latest_remote_commit_sha(owner: str, repo: str, branch: str, token: str) -> str:
    """ SHA stands for Secure Hash Algorithm. It's a unique identifier for a commit.
    https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#get-a-reference """
    try:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        return response.json()["object"]["sha"]
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


def get_remote_file_content(
        file_path: str,  # Ex) 'src/main.py'
        owner: str,
        ref: str,  # Ex) 'main'
        repo: str,
        token: str
        ) -> str:
    """ @link https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28 """
    url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers: dict[str, str] = create_headers(token=token)

    try:
        response: requests.Response = requests.get(
            url=url,
            headers=headers,
            timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        encoded_content: str = response.json()["content"]
        decoded_content: str = base64.b64decode(s=encoded_content).decode(encoding="utf-8")
        # print(f"```{file_path}:\n{decoded_content}```")
        return decoded_content
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


def get_remote_file_tree(owner: str, repo: str, ref: str, token: str) -> list[str]:
    """ Get the file tree of a GitHub repository. """
    try:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1",
            headers=create_headers(token=token),
            timeout=TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        return [item["path"] for item in response.json()["tree"]]
    except requests.exceptions.HTTPError as e:
        logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(msg=f"Error: {e}")
        raise


async def verify_webhook_signature(request: Request, secret: str) -> None:
    """ Verify the webhook signature for security """
    signature: str | None = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        raise ValueError("Missing webhook signature")
    body: bytes = await request.body()

    # Compare the computed signature with the one in the headers
    hmac_key: bytes = secret.encode()
    hmac_signature: str = hmac.new(key=hmac_key, msg=body, digestmod=hashlib.sha256).hexdigest()
    expected_signature: str = "sha256=" + hmac_signature
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid webhook signature")
