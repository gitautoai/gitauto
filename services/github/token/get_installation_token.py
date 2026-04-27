import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.token.get_jwt import get_jwt
from services.github.utils.create_headers import create_headers
from services.supabase.installations.delete_installation import delete_installation
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
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
        raw_token = response.json()["token"]
        if not isinstance(raw_token, str):
            logger.error(
                "get_installation_access_token: non-string token for installation %s",
                installation_id,
            )
            raise ValueError(
                f"GitHub returned non-string token for installation {installation_id}"
            )

        token = raw_token
        logger.info(
            "get_installation_access_token: minted token for installation %s",
            installation_id,
        )
        return token

    # Handle old installations suspended before April 28, 2025 (before suspend webhook was introduced)
    except requests.exceptions.HTTPError as err:
        if (
            err.response.status_code == 403
            and "This installation has been suspended" in err.response.text
        ) or err.response.status_code == 404:
            logger.warning(
                "get_installation_access_token: installation %s suspended or deleted",
                installation_id,
            )
            # 403: Installation suspended, 404: Installation doesn't exist (deleted/uninstalled)
            delete_installation(
                platform="github",
                installation_id=installation_id,
                user_id=0,
                user_name="System",
            )
            raise ValueError(
                f"Installation {installation_id} suspended or deleted"
            ) from err

        raise
