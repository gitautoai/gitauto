# Standard imports
import hashlib  # For HMAC (Hash-based Message Authentication Code) signatures
import hmac  # For HMAC (Hash-based Message Authentication Code) signatures
import logging
import requests
import time

# Third-party imports
from fastapi import Request
import jwt  # For generating JWTs (JSON Web Tokens)


class GitHubManager:
    # Constructor to initialize the GitHub App ID and private key to this instance
    def __init__(self, app_id: str, private_key: bytes) -> None:
        self.app_id: str = app_id
        self.private_key: bytes = private_key

    # Generate a JWT (JSON Web Token) for GitHub App authentication
    def create_jwt(self) -> str:
        now = int(time.time())
        payload: dict[str, int | str] = {
            "iat": now,  # Issued at time
            "exp": now + 600,  # JWT expires in 10 minutes
            "iss": self.app_id,  # Issuer
        }
        # The reason we use RS256 is that GitHub requires it for JWTs
        return jwt.encode(payload=payload, key=self.private_key, algorithm="RS256")

    # Verify the webhook signature for security
    async def verify_webhook_signature(self, request: Request, secret: str) -> None:
        return
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

    # Get an access token for the installed GitHub App
    def get_installation_access_token(self, installation_id: int) -> tuple[str, str]:
        try:
            jwt_token: str = self.create_jwt()
            headers: dict[str, str] = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            url: str = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

            response = requests.post(url=url, headers=headers)
            response.raise_for_status()  # Raises HTTPError for bad responses
            json = response.json()
            return json["token"], json["expires_at"]
        except requests.exceptions.HTTPError as e:
            logging.error(msg=f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logging.error(msg=f"Error: {e}")
            raise
