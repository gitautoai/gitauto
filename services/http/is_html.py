import requests

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_html(response: requests.Response):
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        logger.info("is_html: detected via Content-Type header")
        return True

    # Fallback: check if body starts with HTML doctype/tag
    first_500 = response.text[:500].lstrip()
    result = first_500.startswith("<!DOCTYPE") or first_500.startswith("<html")
    if result:
        logger.info("is_html: detected via body inspection")
    return result
