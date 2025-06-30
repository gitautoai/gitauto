# Standard imports
import logging
from datetime import datetime

# Local imports
from config import EXCEPTION_OWNERS, FREE_TIER_REQUEST_AMOUNT, TZ, DEFAULT_TIME
from services.supabase.installations.get_stripe_customer_id import (
    get_stripe_customer_id,
)
from services.supabase.usage.count_completed_unique_requests import (
    count_completed_unique_requests,
)
from services.stripe.get_base_request_limit import get_base_request_limit
from services.stripe.get_subscription import get_subscription
from services.stripe.parse_subscription_object import parse_subscription_object
from utils.error.handle_exceptions import handle_exceptions

DEFAULT = (False, 0, 1, DEFAULT_TIME)


@handle_exceptions(default_return_value=DEFAULT, raise_on_error=False)
def is_request_limit_reached(
    installation_id: int,
    owner_id: int,
    owner_name: str,
    owner_type: str = None,
    repo_name: str = None,
    issue_number: int = None,
):
    # Exception owners are never limited
    if owner_name in EXCEPTION_OWNERS:
        return (False, 999999, 999999, DEFAULT_TIME)

    # Get Stripe customer ID
    stripe_customer_id = get_stripe_customer_id(installation_id)
    if not stripe_customer_id:
        msg = f"No Stripe Customer ID found for installation {installation_id} owner {owner_id}"
        logging.warning(msg)
        return (True, 0, FREE_TIER_REQUEST_AMOUNT, DEFAULT_TIME)

    # Get subscription data using existing function
    subscription = get_subscription(customer_id=stripe_customer_id)
    start_date_seconds, end_date_seconds, product_id, interval, quantity = (
        parse_subscription_object(
            subscription=subscription,
            installation_id=installation_id,
            customer_id=stripe_customer_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    )

    # Calculate request limit
    base_request_limit = get_base_request_limit(product_id)
    request_limit = (
        base_request_limit * 12 * quantity
        if interval == "year"
        else base_request_limit * quantity
    )

    start_date = datetime.fromtimestamp(timestamp=start_date_seconds, tz=TZ)
    end_date = datetime.fromtimestamp(timestamp=end_date_seconds, tz=TZ)

    # Get completed requests count
    unique_requests = count_completed_unique_requests(installation_id, start_date)

    # Check if current request is a retry
    is_retried = False
    if owner_type and repo_name and issue_number:
        current_request = f"{owner_type}/{owner_name}/{repo_name}#{issue_number}"
        is_retried = current_request in unique_requests

    # Calculate requests left
    requests_left = request_limit - len(unique_requests)

    # If it's a retry, don't count it as hitting the limit
    if is_retried:
        return (False, requests_left, request_limit, end_date)

    # Check if limit is reached
    is_limit_reached = requests_left <= 0

    return (is_limit_reached, requests_left, request_limit, end_date)
