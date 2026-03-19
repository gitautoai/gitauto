# https://docs.powertools.aws.dev/lambda/python/latest/core/logger/
# https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html
import logging
from typing import cast

from aws_lambda_powertools import Logger

from constants.general import IS_PRD, PRODUCT_NAME
from constants.triggers import Trigger

if IS_PRD:
    logger = Logger(service=PRODUCT_NAME, log_uncaught_exceptions=True)
else:
    # Use standard Python logging locally for cleaner output
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(PRODUCT_NAME)


def clear_state():
    """Clear all custom keys to prevent metadata bleeding between Lambda invocations."""
    if IS_PRD:
        cast(Logger, logger).clear_state()


def set_request_id(request_id: str):
    """Set AWS Lambda request ID for current context."""
    if IS_PRD:
        cast(Logger, logger).append_keys(request_id=request_id)


def set_owner_repo(owner: str, repo: str):
    """Set GitHub owner and repo for current context."""
    if IS_PRD and owner and repo:
        cast(Logger, logger).append_keys(owner_repo=f"{owner}/{repo}")


def set_pr_number(pr_number: int):
    """Set PR number for current context."""
    if IS_PRD and pr_number:
        cast(Logger, logger).append_keys(pr_number=pr_number)


def set_event_action(event_name: str, action: str):
    """Set webhook event name and action for log filtering."""
    if IS_PRD and event_name and action:
        cast(Logger, logger).append_keys(event_action=f"{event_name}_{action}")


def set_trigger(trigger: Trigger):
    """Set trigger name for current context."""
    if IS_PRD and trigger:
        cast(Logger, logger).append_keys(trigger=trigger)
