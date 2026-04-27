import os

from utils.env.get_internal_env_var_names import get_internal_env_var_names
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


# default_return_value is intentionally an empty dict, not os.environ.copy(): if scrubbing fails, fail closed (subprocess gets no env, breaks loudly) rather than fail open (subprocess inherits everything, silently leaks the secrets we built this function to scrub — Sentry AGENT-3KJ et al.).
@handle_exceptions(default_return_value={}, raise_on_error=False)
def passthrough_env_for_subprocess():
    """os.environ minus GitAuto-internal secrets. Hand this as `env=` to subprocess.run so customer code can't read our credentials."""
    scrub = get_internal_env_var_names()
    passthrough = {k: v for k, v in os.environ.items() if k not in scrub}
    logger.info(
        "passthrough_env_for_subprocess: %d kept, %d scrubbed",
        len(passthrough),
        len(os.environ) - len(passthrough),
    )
    return passthrough
