import os

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.system.read_os_release_pretty_name import read_os_release_pretty_name


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_runtime_description():
    """Return a one-line description of where this code is executing, detected at call time so the runtime label updates automatically when our Lambda runtime / OS upgrades. Used for the `source` argument of `label_log_source(log, "ours", source)`.
    Output examples:
      - On Lambda AL2023 (today): "AWS Lambda, Amazon Linux 2023"
      - On Lambda AL2024 (post-upgrade, no code change): "AWS Lambda, Amazon Linux 2024"
      - On a dev machine: empty string (we don't tag logs in dev runs)"""
    parts: list[str] = []

    # Presence of AWS_LAMBDA_FUNCTION_NAME signals "we're inside Lambda". The function name itself is internal naming we don't surface.
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        logger.info("get_runtime_description: detected AWS Lambda invocation")
        parts.append("AWS Lambda")
    else:
        logger.info("get_runtime_description: not running in AWS Lambda")

    pretty_name = read_os_release_pretty_name()
    if pretty_name:
        logger.info("get_runtime_description: detected OS pretty name=%s", pretty_name)
        parts.append(pretty_name)
    else:
        logger.info("get_runtime_description: no OS pretty name detected")

    description = ", ".join(parts)
    logger.info("get_runtime_description: returning %s", description)
    return description
