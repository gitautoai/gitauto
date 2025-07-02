import requests
from config import TIMEOUT
from constants.urls import BASE_URL
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_default_structured_rules():
    url = f"{BASE_URL}/api/structured-rules-default"
    response = requests.get(url=url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()
