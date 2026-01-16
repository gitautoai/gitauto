# https://docs.powertools.aws.dev/lambda/python/latest/core/logger/
# https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html
from aws_lambda_powertools import Logger

# POWERTOOLS_DEV=true in .env for human-readable local logs
# In production, logs are JSON formatted
logger = Logger(service="gitauto", log_uncaught_exceptions=True)


def set_request_id(request_id: str):
    """Set AWS Lambda request ID for current context."""
    logger.append_keys(request_id=request_id)


def set_owner_repo(owner: str, repo: str):
    """Set GitHub owner and repo for current context."""
    if owner and repo:
        logger.append_keys(owner_repo=f"{owner}/{repo}")


def set_pr_number(pr_number: int):
    """Set PR number for current context."""
    if pr_number:
        logger.append_keys(pr_number=pr_number)


def set_trigger(trigger: str):
    """Set trigger name for current context."""
    if trigger:
        logger.append_keys(trigger=trigger)
