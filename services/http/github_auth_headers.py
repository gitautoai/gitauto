from urllib.parse import urlparse

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


GITHUB_PRIVATE_HOSTS = {
    # Public REST API: private repo content needs a token to get past 404.
    "api.github.com",
    # Raw file service: 404 without auth for private repos, so we must send a token.
    "raw.githubusercontent.com",
}


@handle_exceptions(default_return_value={}, raise_on_error=False)
def github_auth_headers(url: str, token: str | None):
    """Return Authorization header dict when the URL targets a GitHub host that
    serves private-repo content and we have an installation token to send."""
    if not token:
        logger.info("github_auth_headers: no token available, returning empty")
        return {}

    host = urlparse(url).hostname
    if host not in GITHUB_PRIVATE_HOSTS:
        logger.info("github_auth_headers: host %s not GitHub, returning empty", host)
        return {}

    logger.info("github_auth_headers: adding Authorization for host %s", host)
    return {"Authorization": f"Bearer {token}"}
