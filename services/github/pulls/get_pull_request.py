import requests
from config import TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=("", ""), raise_on_error=False)
def get_pull_request(url: str, token: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#get-a-pull-request"""
    headers = create_headers(token=token)
    res = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    res.raise_for_status()
    res_json = res.json()
    title: str = res_json["title"]
    body: str = res_json["body"]
    return title, body
