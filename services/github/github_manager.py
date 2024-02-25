# Standard imports
import hashlib  # For HMAC (Hash-based Message Authentication Code) signatures
import hmac  # For HMAC (Hash-based Message Authentication Code) signatures
import logging
# import os
import time
from uuid import UUID

# Third-party imports
import jwt  # For generating JWTs (JSON Web Tokens)
import requests
from fastapi import Request
from git import Repo

# Local imports
from config import GITHUB_API_VERSION, TIMEOUT_IN_SECONDS
from services.github.github_types import IssueInfo, RepositoryInfo


class GitHubManager:
    """ Class to manage GitHub App authentication and API requests """

    def __init__(self, app_id: str, private_key: bytes) -> None:
        """ Constructor to initialize the GitHub App ID and private key to this instance """
        self.app_id: str = app_id
        self.private_key: bytes = private_key

    def clone_repository(self, token: str, repo_url: str, uuid: UUID) -> str:
        repo_clone_path: str = f'./tmp/{uuid}'

        # Remove the https:// prefix if it's already in the repo_url
        normalized_repo_url: str = repo_url
        if normalized_repo_url.startswith('https://'):
            normalized_repo_url = normalized_repo_url[8:]

        Repo.clone_from(url=f'https://x-access-token:{token}@{normalized_repo_url}', to_path=repo_clone_path)
        return repo_clone_path

    def create_jwt(self) -> str:
        """ Generate a JWT (JSON Web Token) for GitHub App authentication """
        now = int(time.time())
        payload: dict[str, int | str] = {
            "iat": now,  # Issued at time
            "exp": now + 600,  # JWT expires in 10 minutes
            "iss": self.app_id,  # Issuer
        }
        # The reason we use RS256 is that GitHub requires it for JWTs
        return jwt.encode(payload=payload, key=self.private_key, algorithm="RS256")

    def create_pull_request(self, repo: RepositoryInfo, branch_name: str, issue: IssueInfo, token: str) -> requests.Response:
        """ Create a pull request for a GitHub repository """
        repo_name: str = repo["name"]
        repo_owner: str = repo["owner"]["login"]
        pr_url: str = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
        pr_headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        data: dict[str, str] = {
            "title": issue['title'],
            "body": "TODO: Pull Request Body Text Here",
            "head": f"{repo_owner}:{branch_name}",
            "base": repo["default_branch"],
        }

        try:
            response: requests.Response = requests.post(url=pr_url, headers=pr_headers, json=data, timeout=TIMEOUT_IN_SECONDS)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as http_error:
            logging.error(msg=f"HTTP Error: {http_error.response.status_code} - {http_error.response.text}")
            raise
        except Exception as e:
            logging.error(msg=f"Error: {e}")
            raise

    # def detect_modified_files(self, repo: Repo) -> list[str]:
    #     """ Detect modified files that are already tracked by Git. """
    #     return [item.a_path for item in repo.index.diff(other=None) if item.change_type != 'D']

    # def detect_new_files(self, repo: Repo) -> list[str]:
    #     return repo.untracked_files

    # def detect_removed_files(self, repo: Repo) -> list[str]:
    #     """ Detect files removed from the filesystem but still tracked by Git. """
    #     return [item.a_path for item in repo.index.diff(other=None) if item.change_type == 'D']

    def get_installation_access_token(self, installation_id: int) -> str:
        """ Get an access token for the installed GitHub App """
        try:
            jwt_token: str = self.create_jwt()
            headers: dict[str, str] = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
            }
            url: str = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

            response: requests.Response = requests.post(url=url, headers=headers, timeout=TIMEOUT_IN_SECONDS)
            response.raise_for_status()  # Raises HTTPError for bad responses
            json = response.json()
            return json["token"]
        except requests.exceptions.HTTPError as e:
            logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logging.error(msg=f"Error: {e}")
            raise

    # def get_repository_file_tree(self, repo: Repo) -> list[str]:
    #     return [item.a_path for item in repo.tree().traverse()]

    # def remove_files(self, repo: Repo, files_to_remove: list[str]) -> None:
    #     """ Remove specified files from the Git repository. """
    #     for file in files_to_remove:
    #         if not os.path.exists(os.path.join(repo_path, file)):
    #             repo.git.rm(file)

    # def stage_files(self, repo: Repo, files_to_stage: list[str]) -> None:
    #     """ Stage specified files in the Git repository. """
    #     for file in files_to_stage:
    #         repo.git.add(file)

    async def verify_webhook_signature(self, request: Request, secret: str) -> None:
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
