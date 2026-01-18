# Standard imports
from json import dumps

# Third party imports
from fastapi import HTTPException, Request

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def verify_jira_webhook(request: Request):
    """Verify that the request came from Atlassian Forge"""
    logger.info("Request Headers: %s", dumps(dict(request.headers), indent=2))

    # Verify that the request came from Atlassian Forge
    user_agent = request.headers.get("user-agent", "")
    has_b3_headers = all(
        [request.headers.get("x-b3-traceid"), request.headers.get("x-b3-spanid")]
    )

    if "node-fetch" not in user_agent or not has_b3_headers:
        logger.warning("Not a valid Forge request")
        raise HTTPException(status_code=401, detail="Invalid request source")

    payload = await request.json()
    return payload
