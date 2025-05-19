# Standard imports
import os

# Third party imports
import requests

# Local imports
from config import TIMEOUT
from constants.general import IS_PRD
from utils.error.handle_exceptions import handle_exceptions

URL = os.getenv("SLACK_WEBHOOK_URL_NOTIFICATIONS")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def slack(text: str):
    if not URL and IS_PRD:
        raise ValueError("SLACK_WEBHOOK_URL_NOTIFICATIONS is not set")
    if not URL:
        return None
    requests.post(URL, json={"text": text}, timeout=TIMEOUT)
    return None
