# Standard imports
import base64
import hashlib  # For HMAC (Hash-based Message Authentication Code) signatures
import hmac  # For HMAC (Hash-based Message Authentication Code) signatures
import logging
import time
from typing import Any
from uuid import UUID

# Third-party imports
import jwt  # For generating JWTs (JSON Web Tokens)
import requests
from fastapi import Request
from git import Repo

# Local imports
from config import GITHUB_API_URL, GITHUB_API_VERSION, TIMEOUT_IN_SECONDS


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

        Repo.clone_from(
            url=f'https://x-access-token:{token}@{normalized_repo_url}',
            to_path=repo_clone_path
        )
        return repo_clone_path

    def create_headers(self, token: str) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

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

    def create_pull_request(
            self,
            base: str,  # The branch name you want to merge your changes into
            body: str,
            head: str,
            owner: str,
            repo: str,
            title: str,
            token: str
            ) -> dict[str, Any]:
        url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
        headers: dict[str, str] = self.create_headers(token=token)
        data: dict[str, str] = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }

        try:
            response: requests.Response = requests.post(
                url=url,
                headers=headers,
                json=data,
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
            self,
            branch_name: str,
            owner: str,
            repo: str,
            sha: str,
            token: str
            ) -> None:
        url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs"
        headers: dict[str, str] = self.create_headers(token=token)
        data: dict[str, str] = {"ref": f"refs/heads/{branch_name}", "sha": sha}

        try:
            response: requests.Response = requests.post(
                url=url,
                headers=headers,
                json=data,
                timeout=TIMEOUT_IN_SECONDS
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logging.error(msg=f"Error: {e}")
            raise

    def get_installation_access_token(self, installation_id: int) -> str:
        """ Get an access token for the installed GitHub App """
        jwt_token: str = self.create_jwt()
        headers: dict[str, str] = self.create_headers(token=jwt_token)
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

    def get_remote_file_content(
            self,
            file_path: str,  # Ex) 'src/main.py'
            owner: str,
            ref: str,  # Ex) 'main'
            repo: str,
            token: str
            ) -> str:
        """ @link https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28 """
        url: str = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
        headers: dict[str, str] = self.create_headers(token=token)

        try:
            response: requests.Response = requests.get(
                url=url,
                headers=headers,
                timeout=TIMEOUT_IN_SECONDS
            )
            response.raise_for_status()
            encoded_content: str = response.json()["content"]
            decoded_content: str = base64.b64decode(s=encoded_content).decode(encoding="utf-8")
            print(f"Content of {file_path}: {decoded_content}")
            return decoded_content
        except requests.exceptions.HTTPError as e:
            logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logging.error(msg=f"Error: {e}")
            raise

    def get_remote_file_tree(self, owner: str, repo: str, ref: str, token: str) -> list[str]:
        """ Get the file tree of a GitHub repository. """
        try:
            response: requests.Response = requests.get(
                url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1",
                headers=self.create_headers(token=token),
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
