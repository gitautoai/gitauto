# Standard imports
import time

# Third-party imports
import jwt

# Local imports
from config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_jwt():
    """Generate a JWT (JSON Web Token) for GitHub App authentication"""
    now = int(time.time())
    payload: dict[str, int | str] = {
        "iat": now,  # Issued at time
        "exp": now + 600,  # JWT expires in 10 minutes
        "iss": GITHUB_APP_ID,  # Issuer
    }
    # The reason we use RS256 is that GitHub requires it for JWTs
    return jwt.encode(payload=payload, key=GITHUB_PRIVATE_KEY, algorithm="RS256")
