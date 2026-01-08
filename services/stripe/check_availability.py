from datetime import datetime
from typing import TypedDict

from services.stripe.get_billing_type import get_billing_type, BillingType
from services.stripe.get_paid_subscription import get_paid_subscription
from services.stripe.check_subscription_limit import check_subscription_limit
from services.supabase.owners.get_stripe_customer_id import get_stripe_customer_id
from services.supabase.owners.get_owner import get_owner
from services.vercel.trigger_auto_reload import trigger_auto_reload
from utils.text.get_subscription_limit_message import get_subscription_limit_message
from utils.text.get_insufficient_credits_message import get_insufficient_credits_message
from utils.error.handle_exceptions import handle_exceptions


class AvailabilityStatus(TypedDict):
    can_proceed: bool
    billing_type: BillingType
    requests_left: int | None
    credit_balance_usd: int
    period_end_date: datetime | None
    user_message: str
    log_message: str


DEFAULT_AVAILABILITY_STATUS: AvailabilityStatus = {
    "can_proceed": False,
    "billing_type": "credit",
    "requests_left": None,
    "credit_balance_usd": 0,
    "period_end_date": None,
    "user_message": "Error checking availability",
    "log_message": "Error checking availability",
}


@handle_exceptions(
    default_return_value=DEFAULT_AVAILABILITY_STATUS, raise_on_error=False
)
def check_availability(
    owner_id: int,
    owner_name: str,
    repo_name: str,
    installation_id: int,
    sender_name: str,
):
    """Check if user can proceed based on their billing type and limits."""
    stripe_customer_id = get_stripe_customer_id(owner_id)
    paid_subscription = (
        get_paid_subscription(customer_id=stripe_customer_id)
        if stripe_customer_id
        else None
    )
    billing_type = get_billing_type(
        owner_name=owner_name,
        stripe_customer_id=stripe_customer_id,
        paid_subscription=paid_subscription,
    )

    availability_status: AvailabilityStatus = {
        "can_proceed": False,
        "billing_type": billing_type,
        "requests_left": None,
        "credit_balance_usd": 0,
        "period_end_date": None,
        "user_message": "",
        "log_message": "",
    }

    if billing_type == "exception":
        availability_status["can_proceed"] = True
        availability_status["log_message"] = "Exception owner - unlimited access."

    elif billing_type == "subscription":
        subscription_limit = check_subscription_limit(
            paid_subscription=paid_subscription,
            installation_id=installation_id,
        )
        availability_status["can_proceed"] = subscription_limit["can_proceed"]
        availability_status["requests_left"] = subscription_limit["requests_left"]
        availability_status["period_end_date"] = subscription_limit["period_end_date"]
        if not availability_status["can_proceed"]:
            availability_status["user_message"] = get_subscription_limit_message(
                user_name=sender_name,
                request_limit=subscription_limit["request_limit"],
                period_end_date=subscription_limit["period_end_date"],
            )
            availability_status["log_message"] = (
                f"Request limit reached for {owner_name}/{repo_name}"
            )
        else:
            availability_status["log_message"] = (
                f"Checked subscription limit. {subscription_limit['requests_left']} requests left."
            )

    elif billing_type == "credit":
        owner = get_owner(owner_id=owner_id)
        credit_balance = owner["credit_balance_usd"] if owner else 0
        availability_status["credit_balance_usd"] = credit_balance

        # Check auto-reload before setting can_proceed (works even when balance is 0 or negative)
        if owner:
            auto_reload_enabled = owner.get("auto_reload_enabled", False)
            auto_reload_threshold = owner.get("auto_reload_threshold_usd", 0)

            # Trigger auto-reload if enabled and balance is at or below threshold
            if auto_reload_enabled and credit_balance <= auto_reload_threshold:
                trigger_auto_reload()

        availability_status["can_proceed"] = credit_balance > 0

        if not availability_status["can_proceed"]:
            availability_status["user_message"] = get_insufficient_credits_message(
                user_name=sender_name
            )
            availability_status["log_message"] = (
                f"Insufficient credits for {owner_name}/{repo_name}"
            )
        else:
            availability_status["log_message"] = (
                f"Checked credit balance. ${credit_balance} remaining."
            )

    return availability_status
