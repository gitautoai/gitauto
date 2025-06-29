import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_user_public_email(username: str, token: str) -> str | None:
    """https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28#get-a-user"""
    # If the user is a bot, the email is not available.
    if "[bot]" in username:
        return None

    # If the user is not a bot, get the user's email
    response: requests.Response = requests.get(
        url=f"{GITHUB_API_URL}/users/{username}",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    user_data: dict = response.json()
    email: str | None = user_data.get("email")
    return email
