# Standard imports
from datetime import datetime
from typing import TypedDict

# Local imports
from config import ONE_YEAR_FROM_NOW, EXCEPTION_OWNERS, TZ
from services.supabase.owners.get_stripe_customer_id import (
    get_stripe_customer_id,
)
from services.supabase.owners.get_owner import get_owner
from services.supabase.usage.count_completed_unique_requests import (
    count_completed_unique_requests,
)
from services.stripe.create_stripe_customer import create_stripe_customer
from services.stripe.get_base_request_limit import get_base_request_limit
from services.stripe.get_paid_subscription import get_paid_subscription
from services.supabase.owners.update_stripe_customer_id import update_stripe_customer_id
from utils.error.handle_exceptions import handle_exceptions


class RequestLimitResult(TypedDict):
    is_limit_reached: bool
    requests_left: int
    request_limit: int
    end_date: datetime
    is_credit_user: bool
    credit_balance_usd: int


DEFAULT = {
    "is_limit_reached": False,
    "requests_left": 0,
    "request_limit": 1,
    "end_date": ONE_YEAR_FROM_NOW,
    "is_credit_user": False,
    "credit_balance_usd": 0,
}


@handle_exceptions(default_return_value=DEFAULT, raise_on_error=False)
def is_request_limit_reached(
    installation_id: int,
    owner_id: int,
    owner_name: str,
    owner_type: str = None,
    repo_name: str = None,
    issue_number: int = None,
) -> RequestLimitResult:
    # Exception owners are never limited
    if owner_name in EXCEPTION_OWNERS:
        return {
            "is_limit_reached": False,
            "requests_left": 999999,
            "request_limit": 999999,
            "end_date": ONE_YEAR_FROM_NOW,
            "is_credit_user": False,
            "credit_balance_usd": 0,
        }

    # Get Stripe customer ID
    stripe_customer_id = get_stripe_customer_id(owner_id)
    if not stripe_customer_id:
        # Create Stripe customer with available info (use defaults for missing user info)
        stripe_customer_id = create_stripe_customer(
            owner_id=owner_id,
            owner_name=owner_name,
            installation_id=installation_id,
            user_id=0,  # Default when user info not available
            user_name="unknown",  # Default when user info not available
        )

        if stripe_customer_id:
            # Update owner record with new stripe customer ID
            update_stripe_customer_id(owner_id, stripe_customer_id)
        else:
            # If customer creation failed, block the request
            return {
                "is_limit_reached": True,
                "requests_left": 0,
                "request_limit": 0,
                "end_date": ONE_YEAR_FROM_NOW,
                "is_credit_user": False,
                "credit_balance_usd": 0,
            }

    # Check if user has a paid subscription
    paid_subscription = get_paid_subscription(customer_id=stripe_customer_id)
    has_paid_subscription = paid_subscription is not None

    # If user has paid subscription, use existing logic
    if has_paid_subscription:
        # Extract subscription details from the paid subscription
        item = paid_subscription["items"]["data"][0]  # Get first item

        start_date_seconds = paid_subscription.current_period_start
        end_date_seconds = paid_subscription.current_period_end
        product_id = item["price"]["product"]
        interval = item["price"]["recurring"]["interval"]
        quantity = item["quantity"]

        # Calculate request limit
        base_request_limit = get_base_request_limit(product_id)
        request_limit = (
            base_request_limit * 12 * quantity
            if interval == "year"
            else base_request_limit * quantity
        )
    else:
        # User doesn't have paid subscription, check credit balance
        owner = get_owner(owner_id)
        if not owner or owner["credit_balance_usd"] <= 0:
            credit_balance = owner["credit_balance_usd"] if owner else 0
            return {
                "is_limit_reached": True,
                "requests_left": 0,
                "request_limit": 0,
                "end_date": ONE_YEAR_FROM_NOW,
                "is_credit_user": True,
                "credit_balance_usd": credit_balance,
            }

        # For credits, we don't have a monthly limit - just check if they have balance
        request_limit = 999999  # Effectively unlimited as long as they have credits
        start_date_seconds = int(ONE_YEAR_FROM_NOW.timestamp())
        end_date_seconds = int(ONE_YEAR_FROM_NOW.timestamp())

    # Set credit user flag and get credit balance
    is_credit_user = not has_paid_subscription
    owner = get_owner(owner_id)
    credit_balance = owner["credit_balance_usd"] if owner else 0

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
        return {
            "is_limit_reached": False,
            "requests_left": requests_left,
            "request_limit": request_limit,
            "end_date": end_date,
            "is_credit_user": is_credit_user,
            "credit_balance_usd": credit_balance,
        }

    # Check if limit is reached
    is_limit_reached = requests_left <= 0

    return {
        "is_limit_reached": is_limit_reached,
        "requests_left": requests_left,
        "request_limit": request_limit,
        "end_date": end_date,
        "is_credit_user": is_credit_user,
        "credit_balance_usd": credit_balance,
    }
