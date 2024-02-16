import datetime
import hashlib  # For HMAC (Hash-based Message Authentication Code) signatures
import hmac  # For HMAC (Hash-based Message Authentication Code) signatures
import jwt  # For generating JWTs (JSON Web Tokens)
import requests


class GitHubManager:
    def __init__(self, app_identifier, private_key):
        self.app_identifier = app_identifier
        self.private_key = private_key

    # Generate a JWT (JSON Web Token) for GitHub App authentication
    def create_jwt(self):
        now = int(datetime.datetime.utcnow().timestamp())
        payload = {
            "iat": now,  # Issued at time
            "exp": now + (10 * 60),  # JWT expires in 10 minutes
            "iss": self.app_identifier,  # Issuer
            "sub": self.app_identifier  # Subject
        }
        # The reason we use RS256 is that GitHub requires it for JWTs
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    # Verify the webhook signature for security
    async def verify_webhook_signature(self, request, secret):
        signature = request.headers.get("X-Hub-Signature-256")
        body = await request.body()

        # Compare the computed signature with the one in the headers
        expected_signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid webhook signature")

    # Get an access token for the installed GitHub App
    def get_installation_access_token(self, installation_id):
        jwt_token = self.create_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()["token"]