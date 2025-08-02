from datetime import datetime

from config import PRODUCT_ID
from services.github.comments.create_comment import create_comment
from services.github.types.github_types import BaseArgs
from services.supabase.usage.is_request_limit_reached import is_request_limit_reached
from utils.error.handle_exceptions import handle_exceptions
from utils.text.text_copy import request_issue_comment, request_limit_reached


@handle_exceptions(default_return_value=None, raise_on_error=False)
def combine_and_create_comment(
    base_comment: str,
    installation_id: int,
    owner_id: int,
    owner_name: str,
    owner_type: str,
    repo_name: str,
    issue_number: int,
    sender_name: str,
    base_args: BaseArgs,
) -> None:
    # Check usage limits
    limit_result = is_request_limit_reached(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repo_name=repo_name,
        issue_number=issue_number,
    )
    is_limit_reached = limit_result["is_limit_reached"]
    requests_left = limit_result["requests_left"]
    request_limit = limit_result["request_limit"]
    end_date = limit_result["end_date"]
    is_credit_user = limit_result["is_credit_user"]
    credit_balance_usd = limit_result["credit_balance_usd"]

    # Build comment body
    body = base_comment

    # Add product ID if not gitauto
    if PRODUCT_ID != "gitauto" and "Generate" in body:
        body = body.replace("Generate Tests", f"Generate Tests - {PRODUCT_ID}")
        body = body.replace("Generate PR", f"Generate PR - {PRODUCT_ID}")

    # Add usage info if end_date is valid
    if end_date != datetime(year=1, month=1, day=1, hour=0, minute=0, second=0):
        body += request_issue_comment(
            requests_left=requests_left,
            sender_name=sender_name,
            end_date=end_date,
            is_credit_user=is_credit_user,
            credit_balance_usd=credit_balance_usd,
        )

    # Override with limit reached message if needed
    if is_limit_reached:
        body = request_limit_reached(
            user_name=sender_name,
            request_count=request_limit,
            end_date=end_date,
        )

    # Create the comment
    create_comment(body=body, base_args=base_args)
