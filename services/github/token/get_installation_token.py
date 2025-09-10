from typing import cast
import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.token.get_jwt import get_jwt
from services.github.utils.create_headers import create_headers
from services.supabase.installations.delete_installation import delete_installation
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_access_token(installation_id: int):
    """https://docs.github.com/en/rest/apps/apps?apiVersion=2022-11-28#create-an-installation-access-token-for-an-app"""
    try:
        jwt_token = get_jwt()
        response = requests.post(
            url=f"{GITHUB_API_URL}/app/installations/{installation_id}/access_tokens",
            headers=create_headers(token=jwt_token),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return cast(str, response.json()["token"])

    # Handle old installations suspended before April 28, 2025 (before suspend webhook was introduced)
    except requests.exceptions.HTTPError as err:
        if (
            err.response.status_code == 403
            and "This installation has been suspended" in err.response.text
        ) or err.response.status_code == 404:
            # 403: Installation suspended, 404: Installation doesn't exist (deleted/uninstalled)
            delete_installation(
                installation_id=installation_id, user_id=0, user_name="System"
            )
            return None

        raise
