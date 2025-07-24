from requests import get
from config import GITHUB_API_URL, TIMEOUT
from services.github.token.get_jwt import get_jwt
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_installation_permissions(installation_id: int):
    # This endpoint requires JWT authentication
    # Generate a fresh JWT for this request
    jwt_token = get_jwt()

    # https://docs.github.com/en/rest/apps/apps?apiVersion=2022-11-28#get-an-installation-for-the-authenticated-app
    url = f"{GITHUB_API_URL}/app/installations/{installation_id}"
    headers = create_headers(token=jwt_token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json().get("permissions", {})
