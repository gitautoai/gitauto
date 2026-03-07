import unicodedata
from dataclasses import dataclass

import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@dataclass
class UserPublicInfo:
    email: str | None
    display_name: str


@handle_exceptions(
    default_return_value=UserPublicInfo(email=None, display_name=""),
    raise_on_error=False,
)
def get_user_public_info(username: str, token: str):
    """https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28#get-a-user"""
    # Bots (e.g. dependabot[bot]) have name=null and email=null on the API, so skip the call
    if "[bot]" in username:
        return UserPublicInfo(email=None, display_name="")

    response: requests.Response = requests.get(
        url=f"{GITHUB_API_URL}/users/{username}",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    # Some usernames (e.g. "Copilot") aren't real GitHub users
    if response.status_code == 404:
        return UserPublicInfo(email=None, display_name="")

    response.raise_for_status()
    user_data: dict[str, str | None] = response.json()
    email = user_data.get("email")

    name: str = user_data.get("name") or ""
    # Normalize: strip Unicode fancy chars + title-case every word
    # Cross-ref: website/utils/normalize-display-name.ts
    name = unicodedata.normalize("NFKC", name).replace(".", " ").title()
    return UserPublicInfo(email=email, display_name=name)
