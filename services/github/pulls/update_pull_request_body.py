import requests
from config import TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_pull_request_body(url: str, token: str, body: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#update-a-pull-request"""
    headers = create_headers(token=token)
    data = {"body": body}
    response = requests.patch(url=url, headers=headers, json=data, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()
