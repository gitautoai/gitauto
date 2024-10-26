    # Add logging for issue assessment and clarification requests
    # Ensure backward compatibility by maintaining existing processes
    handle_issue_event(body, base_args.issue_number, base_args.token)
    # Integrate issue handling into the pull request generation workflow
from services.webhook_handler import handle_issue_event
def assess_issue_details(issue_details):
    """Assess the adequacy of issue details."""
    issue_number = base_args.issue_number
    # Terminate the current processing loop when feedback is requested
    return None
    token = base_args.token
    if not assess_issue_details(body):
        return request_clarification(issue_number, token)
    # Placeholder logic for assessing issue details
    if not issue_details or len(issue_details) < 20:
        return False
    return True

def request_clarification(issue_number, token):
    """Request clarification on an issue by commenting."""
    comment = "The details provided are insufficient for processing. Could you please provide more information?"
    return comment_on_issue(issue_number, comment, token)

# Standard imports
import base64
import hashlib  # For HMAC (Hash-based Message Authentication Code) signatures
import hmac  # For HMAC (Hash-based Message Authentication Code) signatures
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

# Third-party imports
import jwt  # For generating JWTs (JSON Web Tokens)
import requests
from fastapi import Request
from github import Github, GithubException
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Repository import Repository

# Local imports
from config import (
    EXCEPTION_OWNERS,
    GITHUB_API_URL,
    GITHUB_API_VERSION,
    GITHUB_APP_ID,
    GITHUB_APP_IDS,
    GITHUB_APP_NAME,
    GITHUB_ISSUE_DIR,
    GITHUB_ISSUE_TEMPLATES,
    GITHUB_PRIVATE_KEY,
    IS_PRD,
    MAX_RETRIES,
    PRODUCT_NAME,
    PRODUCT_URL,
    TIMEOUT,
    PRODUCT_ID,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    UTF8,
)
from services.github.github_types import (
    BaseArgs,
    GitHubContentInfo,
    GitHubLabeledPayload,
    IssueInfo,
)
from services.openai.vision import describe_image
from services.supabase import SupabaseManager
from utils.file_manager import apply_patch, get_file_content, run_command
from utils.handle_exceptions import handle_exceptions
from utils.parse_urls import parse_github_url
from utils.text_copy import (
    UPDATE_COMMENT_FOR_422,
    UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE,
    request_issue_comment,
    request_limit_reached,
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def add_issue_templates(full_name: str, installer_name: str, token: str) -> None:
    print(f"Adding issue templates to the repo: '{full_name}' by '{installer_name}'.\n")
    gh = Github(login_or_token=token)
    repo: Repository = gh.get_repo(full_name_or_id=full_name)

    # Create a new branch
    default_branch = None
    default_branch_name: str = repo.default_branch
    retries = 0
    while retries < MAX_RETRIES:
        try:
            default_branch = repo.get_branch(branch=default_branch_name)
            break
        except GithubException as e:
            retries += 1
            msg = f"Error: {e.data['message']}. Retrying to get the default branch for repo: {full_name} and branch: {default_branch_name}."
            logging.info(msg)
            time.sleep(20)
    new_branch_name: str = f"{PRODUCT_ID}/add-issue-templates-{str(object=uuid4())}"
    ref = f"refs/heads/{new_branch_name}"
    if default_branch is None:
        msg = f"Error: Could not get the default branch for repo: {full_name} and branch: {default_branch_name}."
        raise RuntimeError(msg)
    repo.create_git_ref(ref=ref, sha=default_branch.commit.sha)

    # Add issue templates to the new branch
    added_templates: list[str] = []
    for template_file in GITHUB_ISSUE_TEMPLATES:
        # Get an issue template content from GitAuto repository
        template_path: str = GITHUB_ISSUE_DIR + "/" + template_file
        content = get_file_content(file_path=template_path)

        # Get the list of existing files in the user's remote repository at the GITHUB_ISSUE_DIR. We need to use try except as repo.get_contents() raises a 404 error if the directory doesn't exist. Also directory path MUST end without a slash.
        try:
            remote_files: list[ContentFile] = repo.get_contents(path=GITHUB_ISSUE_DIR)
            remote_file_names: list[str] = [file.name for file in remote_files]
        except Exception:  # pylint: disable=broad-except
            remote_file_names = []

        # Skip if the template already exists
        if template_file in remote_file_names:
            continue

        # Add file to the new branch
        msg = f"Add a template: {template_file}"
        repo.create_file(
            path=template_path, message=msg, content=content, branch=new_branch_name
        )
        added_templates.append(template_file)

    # Return early if no templates were added
    if not added_templates:
        return

    # If there are added templates, create a PR
    pr: PullRequest = repo.create_pull(
        base=default_branch_name,
        head=new_branch_name,
        # Add X issue templates: bug_report.yml, feature_request.yml
        title=f"Add {len(added_templates)} issue templates",
        body=f"## Overview\n\nThis PR adds issue templates to the repository so that you can create issues more easily for {PRODUCT_NAME} and your project. Please review the changes and merge the PR if you agree.\n\n## Added templates:\n\n- "
        + "\n- ".join(added_templates),
        maintainer_can_modify=True,
        draft=False,
    )

    # Add reviewers to the PR. When I tried to add reviewers, I got a 422 error. So, "reviewers" parameter must be an array of strings, not a string.
    pr.create_review_request(reviewers=[installer_name])


@handle_exceptions(default_return_value=None, raise_on_error=True)
def add_label_to_issue(
    owner: str, repo: str, issue_number: int, label: str, token: str
) -> None:
    """If the label doesn't exist, it will be created. Color will be automatically assigned. If the issue already has the label, no change will be made and no error will be raised. https://docs.github.com/en/rest/issues/labels?apiVersion=2022-11-28#add-labels-to-an-issue"""
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/labels",
        headers=create_headers(token=token),
        json={"labels": [label]},
        timeout=TIMEOUT,
    )
    response.raise_for_status()


@handle_exceptions(default_return_value=None, raise_on_error=False)
def add_reaction_to_issue(issue_number: int, content: str, base_args: BaseArgs) -> None:
    """https://docs.github.com/en/rest/reactions/reactions?apiVersion=2022-11-28#create-reaction-for-an-issue"""
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/reactions",
        headers=create_headers(token=token),
        json={"content": content},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response.json()


@handle_exceptions(default_return_value=False, raise_on_error=False)
def commit_changes_to_remote_branch(
    diff: str, file_path: str, base_args: BaseArgs, message: Optional[str] = None
):
    """https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents"""
    if message is None:
        message = f"Update {file_path}."
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    new_branch = base_args["new_branch"]
    if not new_branch:
        raise ValueError("new_branch is not set.")
    url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)
    get_response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # If 404 error, the file doesn't exist.
    if get_response.status_code == 404:
        original_text, sha = "", ""
    else:
        get_response.raise_for_status()
        file_info: GitHubContentInfo = get_response.json()

        # Return if the file_path is a directory. See Example2 at https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
        if file_info["type"] == "dir":
            return f"file_path: '{file_path}' is a directory. It should be a file path."

        # Get the original text and SHA of the file
        s1: str = file_info.get("content")
        # content is base64 encoded by default in GitHub API
        original_text = base64.b64decode(s=s1).decode(encoding=UTF8, errors="replace")
        sha: str = file_info["sha"]

    # Create a new commit
    modified_text, rej_text = apply_patch(original_text=original_text, diff_text=diff)
    if modified_text == "":
        return f"diff format is incorrect. No changes were made to the file: {file_path}. Review the diff, correct it, and try again.\n\n{diff=}"
    if modified_text != "" and rej_text != "":
        return f"diff partially applied to the file: {file_path}. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\n{diff=}\n\n{rej_text=}"
    s2 = modified_text.encode(encoding=UTF8)
    data: dict[str, str | None] = {
        "message": message,
        "content": base64.b64encode(s=s2).decode(encoding=UTF8),
        "branch": new_branch,
    }
    if sha != "":
        data["sha"] = sha
    put_response = requests.put(
        url=url,
        json=data,
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    put_response.raise_for_status()
    return f"diff applied to the file: {file_path} successfully by {commit_changes_to_remote_branch.__name__}()."


@handle_exceptions(raise_on_error=True)
def create_comment(issue_number: int, body: str, base_args: BaseArgs) -> str:
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment"""
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
        headers=create_headers(token=token),
        json={"body": body},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["url"]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_comment_on_issue_with_gitauto_button(payload: GitHubLabeledPayload) -> None:
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment"""
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)
    owner_name: str = payload["repository"]["owner"]["login"]
    owner_id: int = payload["repository"]["owner"]["id"]
    repo_name: str = payload["repository"]["name"]
    issue_number: int = payload["issue"]["number"]
    user_id: int = payload["sender"]["id"]
    user_name: str = payload["sender"]["login"]

    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # Proper issue generation comment, create user if not exist (first issue in an orgnanization)
    first_issue = False
    if not supabase_manager.user_exists(user_id=user_id):
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
            owner_name=owner_name,
        )
    )

    body = "Click the checkbox below to generate a PR!\n- [ ] Generate PR"
    if PRODUCT_ID != "gitauto":
        body += " - " + PRODUCT_ID

    if end_date != datetime(year=1, month=1, day=1, hour=0, minute=0, second=0):
        body += request_issue_comment(
            requests_left=requests_left, sender_name=user_name, end_date=end_date
        )

    if requests_left <= 0 and IS_PRD and owner_name not in EXCEPTION_OWNERS:
        logging.info("\nRequest limit reached for user %s.", user_name)
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

    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner_name}/{repo_name}/issues/{issue_number}/comments",
        headers=create_headers(token=token),
        json={"body": body},
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    return response.json()


def create_headers(token: str, media_type: Optional[str] = ".v3") -> dict[str, str]:
    """https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api?apiVersion=2022-11-28#headers"""
    return {
        "Accept": f"application/vnd.github{media_type}+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": GITHUB_APP_NAME,
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def create_jwt() -> str:
    """Generate a JWT (JSON Web Token) for GitHub App authentication"""
    now = int(time.time())
    payload: dict[str, int | str] = {
        "iat": now,  # Issued at time
        "exp": now + 600,  # JWT expires in 10 minutes
        "iss": GITHUB_APP_ID,  # Issuer
    }
    # The reason we use RS256 is that GitHub requires it for JWTs
    return jwt.encode(payload=payload, key=GITHUB_PRIVATE_KEY, algorithm="RS256")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_pull_request(body: str, title: str, base_args: BaseArgs) -> str | None:
    """https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request"""
    owner, repo, base, head, token, reviewers = (
        base_args["owner"],
        base_args["repo"],
        base_args["base_branch"],
        base_args["new_branch"],
        base_args["token"],
        base_args["reviewers"],
    )
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
        headers=create_headers(token=token),
        json={"title": title, "body": body, "head": head, "base": base},
        timeout=TIMEOUT,
    )
    if response.status_code == 422:
        msg = f"{create_pull_request.__name__} encountered an HTTPError: 422 Client Error: Unprocessable Entity for url: {response.url}, which is because no commits between the base branch and the working branch."
        print(msg)
        return None
    response.raise_for_status()
    pr_data = response.json()
    pr_number = pr_data["number"]

    # https://docs.github.com/en/rest/pulls/review-requests?apiVersion=2022-11-28#request-reviewers-for-a-pull-request
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
        headers=create_headers(token=token),
        json={"reviewers": reviewers},
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    return pr_data["html_url"]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_remote_branch(sha: str, base_args: BaseArgs) -> None:
    owner, repo, branch_name, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["new_branch"],
        base_args["token"],
    )
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs",
        headers=create_headers(token=token),
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        timeout=TIMEOUT,
    )
    response.raise_for_status()


def initialize_repo(repo_path: str, remote_url: str) -> None:
    """Push an initial empty commit to the remote repository to create a commit sha."""
    if not os.path.exists(path=repo_path):
        os.makedirs(name=repo_path)

    run_command(command="git init", cwd=repo_path)
    with open(file=os.path.join(repo_path, "README.md"), mode="w", encoding=UTF8) as f:
        f.write(f"# Initial commit by [{PRODUCT_NAME}]({PRODUCT_URL})\n")
    run_command(command="git add README.md", cwd=repo_path)
    run_command(command='git commit -m "Initial commit"', cwd=repo_path)
    run_command(command=f"git remote add origin {remote_url}", cwd=repo_path)
    run_command(command="git push -u origin main", cwd=repo_path)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_access_token(installation_id: int) -> str | None:
    """https://docs.github.com/en/rest/apps/apps?apiVersion=2022-11-28#create-an-installation-access-token-for-an-app"""
    jwt_token: str = create_jwt()
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/app/installations/{installation_id}/access_tokens",
        headers=create_headers(token=jwt_token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["token"]


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_installed_owners_and_repos(token: str) -> list[dict[str, int | str]]:
    """https://docs.github.com/en/rest/apps/installations?apiVersion=2022-11-28#list-repositories-accessible-to-the-app-installation"""
    owners_repos = []
    page = 1
    while True:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/installation/repositories",
            headers=create_headers(token=token),
            params={"per_page": 100, "page": page},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        repos = response.json().get("repositories", [])

        # If there are no more repositories, break the loop. Otherwise, add them to the list
        if not repos:
            break
        items: list[dict[str, int | str]] = [
            {
                "owner_id": repo["owner"]["id"],
                "owner": repo["owner"]["login"],
                "repo": repo["name"],
            }
            for repo in repos
        ]
        owners_repos.extend(items)

        # https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28
        print("response.links:", json.dumps(response.links, indent=2))
        if "next" not in response.links:
            break
        page += 1
    return owners_repos


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_issue_comments(
    issue_number: int, base_args: BaseArgs, includes_me: bool = False
) -> list[str]:
    """https://docs.github.com/en/rest/issues/comments#list-issue-comments"""
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    response = requests.get(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    comments: list[dict[str, Any]] = response.json()
    if not includes_me:
        filtered_comments: list[dict[str, Any]] = [
            comment
            for comment in comments
            if comment.get("performed_via_github_app") is None
            or comment["performed_via_github_app"].get("id") not in GITHUB_APP_IDS
        ]
    else:
        filtered_comments = comments
    comment_texts: list[str] = [comment["body"] for comment in filtered_comments]
    return comment_texts


def get_latest_remote_commit_sha(
    unique_issue_id: str, clone_url: str, base_args: BaseArgs
) -> str:
    """SHA stands for Secure Hash Algorithm. It's a unique identifier for a commit.
    https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#get-a-reference"""
    owner, repo, branch, comment_url = (
        base_args["owner"],
        base_args["repo"],
        base_args["base_branch"],
        base_args["comment_url"],
    )
    token = base_args["token"]
    try:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers=create_headers(token=token),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["object"]["sha"]
    except requests.exceptions.HTTPError as e:
        if (
            e.response.status_code == 409
            and e.response.json()["message"] == "Git Repository is empty."
        ):
            logging.info(
                msg="Repository is empty. So, creating an initial empty commit."
            )
            initialize_repo(repo_path=f"/tmp/repo/{owner}-{repo}", remote_url=clone_url)
            return get_latest_remote_commit_sha(
                unique_issue_id=unique_issue_id,
                clone_url=clone_url,
                base_args=base_args,
            )
        raise
    except Exception as e:
        update_comment_for_raised_errors(
            error=e,
            comment_url=comment_url,
            token=token,
            which_function=get_latest_remote_commit_sha.__name__,
        )
        # Raise an error because we can't continue without the latest commit SHA
        raise RuntimeError(
            f"Error: Could not get the latest commit SHA in {get_latest_remote_commit_sha.__name__}"
        ) from e


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_oldest_unassigned_open_issue(
    owner: str, repo: str, token: str
) -> IssueInfo | None:
    """Get an oldest unassigned open issue without "gitauto" label in a repository. https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#list-repository-issues"""
    page = 1
    while True:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues",
            headers=create_headers(token=token),
            params={
                "assignee": "none",  # none, *, or username
                "direction": "asc",  # asc or desc
                "page": page,
                "per_page": 100,
                "sort": "created",  # created, updated, comments
                "state": "open",  # open, closed, or all
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        issues: list[IssueInfo] = response.json()

        # If there are no corresponding issues, return None
        if not issues:
            return None

        # Find the first issue without the PRODUCT_ID label
        for issue in issues:
            if all(label["name"] != PRODUCT_ID for label in issue["labels"]):
                return issue

        # If there are open issues, but all of them have the PRODUCT_ID label, continue to the next page
        page += 1


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_owner_name(owner_id: int, token: str) -> str | None:
    """https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28#get-a-user-using-their-id"""
    response: requests.Response = requests.get(
        url=f"{GITHUB_API_URL}/user/{owner_id}",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["login"]


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_remote_file_content(
    file_path: str,
    base_args: BaseArgs,
    line_number: Optional[int] = None,
    keyword: Optional[str] = None,
) -> str:
    """
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28

    params:
    - file_path: file path or directory path. Ex) 'src/main.py' or 'src'
    - line_number: specific line number to focus on
    - keyword: keyword to search in the file content
    """
    if line_number is not None and keyword is not None:
        return "Error: You can only specify either line_number or keyword, not both."

    owner, repo, ref, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["new_branch"],
        base_args["token"],
    )
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers: dict[str, str] = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # If 404 error, return early. Otherwise, raise a HTTPError
    if response.status_code == 404:
        return f"{get_remote_file_content.__name__} encountered an HTTPError: 404 Client Error: Not Found for url: {url}. Check the file path, correct it, and try again."
    response.raise_for_status()

    # file_path is expected to be a file path, but it can be a directory path due to AI's volatility. See Example2 at https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
    res_json = response.json()
    if not isinstance(res_json, dict):
        file_paths: list[str] = [item["path"] for item in res_json]
        msg = f"Searched directory '{file_path}' and found: {json.dumps(file_paths)}"
        return msg

    encoded_content: str = res_json["content"]  # Base64 encoded content

    # If encoded_content is image, describe the image content in text by vision API
    if file_path.endswith((".png", ".jpeg", ".jpg", ".webp", ".gif")):
        msg = f"Opened image file: '{file_path}' and described the content.\n\n"
        return msg + describe_image(base64_image=encoded_content)

    # Otherwise, decode the content
    decoded_content: str = base64.b64decode(s=encoded_content).decode(encoding=UTF8)
    lines = decoded_content.split("\n")
    numbered_lines = [f"{i + 1}: {line}" for i, line in enumerate(lines)]
    file_path_with_lines = file_path

    # If line_number is specified, show the lines around the line_number
    if line_number is not None:
        start = max(line_number - 6, 0)
        end = min(line_number + 5, len(lines))
        numbered_lines = numbered_lines[start:end]
        file_path_with_lines = f"{file_path}#L{start + 1}-L{end}"

    # If keyword is specified, show the lines containing the keyword
    elif keyword is not None:
        segments = []
        for i, line in enumerate(lines):
            if keyword not in line:
                continue
            start = max(i - 5, 0)
            end = min(i + 6, len(lines))
            segment = "\n".join(numbered_lines[start:end])
            file_path_with_lines = f"{file_path}#L{start + 1}-L{end}"
            segments.append(f"```{file_path_with_lines}\n" + segment + "\n```")

        if not segments:
            return f"Keyword '{keyword}' not found in the file '{file_path}'."
        msg = f"Opened file: '{file_path}' and found multiple occurrences of '{keyword}'.\n\n"
        return msg + "\n\n•••\n\n".join(segments)

    numbered_content: str = "\n".join(numbered_lines)
    msg = f"Opened file: '{file_path}' with line numbers for your information.\n\n"
    output = msg + f"```{file_path_with_lines}\n{numbered_content}\n```"
    return output


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_remote_file_content_by_url(url: str, token: str) -> str:
    """https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28"""
    parts = parse_github_url(url)
    owner, repo, ref, file_path = (
        parts["owner"],
        parts["repo"],
        parts["ref"],
        parts["file_path"],
    )
    start, end = parts["start_line"], parts["end_line"]
    url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers: dict[str, str] = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    response_json = response.json()
    encoded_content: str = response_json["content"]  # Base64 encoded content
    decoded_content: str = base64.b64decode(s=encoded_content).decode(encoding=UTF8)
    numbered_lines = [
        f"{i + 1}: {line}" for i, line in enumerate(decoded_content.split("\n"))
    ]

    if start is not None and end is not None:
        numbered_lines = numbered_lines[start - 1 : end]  # noqa: E203
        file_path_with_lines = f"{file_path}#L{start}-L{end}"
    elif start is not None:
        numbered_lines = numbered_lines[start - 1]  # noqa: E203
        file_path_with_lines = f"{file_path}#L{start}"
    else:
        file_path_with_lines = file_path

    numbered_content: str = "\n".join(numbered_lines)
    return f"## {file_path_with_lines}\n\n{numbered_content}"


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_remote_file_tree(base_args: BaseArgs) -> list[str]:
    """
    Get the file tree of a GitHub repository at a ref branch.
    https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree
    """
    owner, repo, ref = base_args["owner"], base_args["repo"], base_args["base_branch"]
    response = requests.get(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{ref}",
        headers=create_headers(token=base_args["token"]),
        # params={"recursive": 1},  # 0, 1, "true", or "false" are all True!! Just remove it to disable recursion.
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    file_paths = [item["path"] for item in response.json()["tree"]]
    print(f"{len(file_paths)} file or directory paths found in the root directory.")
    return file_paths


@handle_exceptions(default_return_value="", raise_on_error=False)
def search_remote_file_contents(query: str, base_args: BaseArgs) -> str:
    """
    - Only the default branch is considered.
    - Only files smaller than 384 KB are searchable.
    - This endpoint requires you to authenticate and limits you to 10 requests per minute.

    https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28
    https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax
    https://docs.github.com/en/search-github/searching-on-github/searching-in-forks
    """
    owner, repo, is_fork, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["is_fork"],
        base_args["token"],
    )
    q = f"{query} repo:{owner}/{repo}"
    if is_fork:
        q = f"{query} repo:{owner}/{repo} fork:true"
    params = {"q": q, "per_page": 10, "page": 1}  # per_page: max 100
    url = f"{GITHUB_API_URL}/search/code"
    headers: dict[str, str] = create_headers(token=token)
    headers["Accept"] = "application/vnd.github.text-match+json"
    response = requests.get(url=url, headers=headers, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    response_json = response.json()
    files = []
    for item in response_json.get("items", []):
        file_path = item["path"]
        text_matches = item.get("text_matches", [])

        for match in text_matches:
            fragment = match.get("fragment", "")
            files.append(
                f"```A fragment where search query '{query}' matched from {file_path}\n{fragment}\n```"
            )
    msg = f"{len(files)} files found for the search query '{query}'\n"
    print(msg)
    output = msg + "\n" + "\n\n".join(files)
    return output


@handle_exceptions(default_return_value=None, raise_on_error=False)
def turn_on_issue(full_name: str, token: str) -> None:
    """
    We can turn on the issues feature for a repository using the GitHub API.

    [UPDATED] This requires "Administration" permission and it is too strong and not recommended as the permission allows the app to delete the repository. So, we will not use this function. Also we don't turn on the permission so we can't use this function as well.
    """
    gh = Github(login_or_token=token)
    repo: Repository = gh.get_repo(full_name_or_id=full_name)
    if not repo.has_issues:
        repo.edit(has_issues=True)


@handle_exceptions(raise_on_error=True)
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


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_comment(comment_url: str, body: str, token: str) -> dict[str, Any]:
    """https://docs.github.com/en/rest/issues/comments#update-an-issue-comment"""
    print(body + "\n")
    response: requests.Response = requests.patch(
        url=comment_url,
        headers=create_headers(token=token),
        json={"body": body},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def update_comment_for_raised_errors(
    error: Any, comment_url: str, token: str, which_function: str
) -> dict[str, Any]:
    """Update the comment on issue with an error message and raise the error."""
    body = UPDATE_COMMENT_FOR_422
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
                body = UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE
            else:
                logging.error(
                    "%s HTTP Error: %s - %s",
                    which_function,
                    error.response.status_code,
                    error.response.text,
                )
        else:
            logging.error("%s Error: %s", which_function, error)
    except Exception as e:  # pylint: disable=broad-except
        logging.error("%s Error: %s", which_function, e)
    update_comment(comment_url=comment_url, token=token, body=body)

    raise RuntimeError("Error occurred")
