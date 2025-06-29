from base64 import b64encode
from requests import get
from config import TIMEOUT, UTF8
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_base64(url: str) -> str:
    response = get(url=url, timeout=TIMEOUT)
    response.raise_for_status()
    base64_image: str = b64encode(response.content).decode(encoding=UTF8)
    return base64_image
