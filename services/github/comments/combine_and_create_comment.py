from datetime import datetime

from config import PRODUCT_ID

# Local imports (GitHub)
from services.github.comments.create_comment import create_comment

# Local imports (Stripe)
from services.stripe.check_availability import check_availability

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.text.text_copy import request_issue_comment


@handle_exceptions(default_return_value=None, raise_on_error=False)
def combine_and_create_comment(
    *,
    owner_id: int,
    owner_name: str,
    repo_name: str,
    installation_id: int,
    issue_number: int,
    token: str,
    base_comment: str,
    sender_name: str,
):
    # Check availability
    availability_status = check_availability(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        installation_id=installation_id,
        sender_name=sender_name,
    )

    can_proceed = availability_status["can_proceed"]
    user_message = availability_status["user_message"]
    requests_left = availability_status["requests_left"]
    billing_type = availability_status["billing_type"]
    credit_balance_usd = availability_status["credit_balance_usd"]

    # Get period end date for subscription users
    end_date = availability_status.get("period_end_date") or datetime(
        year=1, month=1, day=1, hour=0, minute=0, second=0
    )

    # Build comment body
    body = base_comment

    # Add product ID if not gitauto
    if PRODUCT_ID != "gitauto" and "Generate" in body:
        body = body.replace("Generate Tests", f"Generate Tests - {PRODUCT_ID}")
        body = body.replace("Generate PR", f"Generate PR - {PRODUCT_ID}")

    # Add usage info if end_date is valid
    if end_date != datetime(year=1, month=1, day=1, hour=0, minute=0, second=0):
        body += request_issue_comment(
            requests_left=requests_left or 0,
            sender_name=sender_name,
            end_date=end_date,
            is_credit_user=(billing_type == "credit"),
            credit_balance_usd=credit_balance_usd,
        )

    # Override with limit reached message if needed
    if not can_proceed and user_message:
        body = user_message

    # Create the comment
    create_comment(
        owner=owner_name,
        repo=repo_name,
        token=token,
        issue_number=issue_number,
        body=body,
    )
