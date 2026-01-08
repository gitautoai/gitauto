from datetime import datetime
from typing import TypedDict
from config import TZ, ONE_YEAR_FROM_NOW
from services.supabase.usage.count_completed_unique_requests import (
    count_completed_unique_requests,
)
from services.stripe.get_base_request_limit import get_base_request_limit
from utils.error.handle_exceptions import handle_exceptions


class SubscriptionLimitResult(TypedDict):
    can_proceed: bool
    requests_left: int
    request_limit: int
    period_end_date: datetime


DEFAULT_SUBSCRIPTION_LIMIT: SubscriptionLimitResult = {
    "can_proceed": False,
    "requests_left": 0,
    "request_limit": 0,
    "period_end_date": ONE_YEAR_FROM_NOW,
}


@handle_exceptions(
    default_return_value=DEFAULT_SUBSCRIPTION_LIMIT, raise_on_error=False
)
def check_subscription_limit(
    paid_subscription,
    installation_id: int,
) -> SubscriptionLimitResult:
    item = paid_subscription["items"]["data"][0]
    start_date_seconds = paid_subscription.current_period_start
    end_date_seconds = paid_subscription.current_period_end
    product_id = item["price"]["product"]
    interval = item["price"]["recurring"]["interval"]
    quantity = item["quantity"]

    base_request_limit = get_base_request_limit(product_id)
    request_limit = (
        base_request_limit * 12 * quantity
        if interval == "year"
        else base_request_limit * quantity
    )

    start_date = datetime.fromtimestamp(timestamp=start_date_seconds, tz=TZ)
    end_date = datetime.fromtimestamp(timestamp=end_date_seconds, tz=TZ)

    unique_requests = count_completed_unique_requests(installation_id, start_date)
    requests_left = request_limit - len(unique_requests)
    can_proceed = requests_left > 0

    return {
        "can_proceed": can_proceed,
        "requests_left": requests_left,
        "request_limit": request_limit,
        "period_end_date": end_date,
    }
