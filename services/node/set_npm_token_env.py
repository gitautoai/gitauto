import os

from services.supabase.npm_tokens.get_npm_token import get_npm_token
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def set_npm_token_env(*, platform: Platform, owner_id: int):
    """Set NPM_TOKEN environment variable if available for the owner."""
    npm_token = get_npm_token(platform=platform, owner_id=owner_id)
    if npm_token:
        os.environ["NPM_TOKEN"] = npm_token
        logger.info("NPM_TOKEN set for %s/%s", platform, owner_id)
