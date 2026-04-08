from typing import TypedDict

from services.stripe.get_billing_type import get_billing_type, BillingType
from services.supabase.owners.get_owner import get_owner
from services.vercel.trigger_auto_reload import trigger_auto_reload
from utils.text.get_insufficient_credits_message import get_insufficient_credits_message
from utils.error.handle_exceptions import handle_exceptions


class AvailabilityStatus(TypedDict):
    can_proceed: bool
    billing_type: BillingType
    credit_balance_usd: int
    user_message: str
    log_message: str


DEFAULT_AVAILABILITY_STATUS: AvailabilityStatus = {
    "can_proceed": False,
    "billing_type": "credit",
    "credit_balance_usd": 0,
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
    sender_name: str,
):
    billing_type = get_billing_type(owner_name=owner_name)

    availability_status: AvailabilityStatus = {
        "can_proceed": False,
        "billing_type": billing_type,
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "",
    }

    if billing_type == "exception":
        availability_status["can_proceed"] = True
        availability_status["log_message"] = "Exception owner - unlimited access."

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

                # Re-read balance after auto-reload since trigger_auto_reload is synchronous
                owner = get_owner(owner_id=owner_id)
                credit_balance = owner["credit_balance_usd"] if owner else 0
                availability_status["credit_balance_usd"] = credit_balance

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
