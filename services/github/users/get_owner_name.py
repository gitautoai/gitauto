import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


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
