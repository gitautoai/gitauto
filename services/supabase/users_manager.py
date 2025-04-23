# Standard imports
import logging
from datetime import datetime
from typing import Any

# Third Party imports
import stripe

# Local imports
from config import (
    DEFAULT_TIME,
    GITHUB_NOREPLY_EMAIL_DOMAIN,
    STRIPE_FREE_TIER_PRICE_ID,
    TZ,
)
from services.stripe.customer import (
    get_subscription,
    get_base_request_limit,
    subscribe_to_free_plan,
)
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


def check_email_is_valid(email: str | None) -> bool:
    if email is None:
        return False
    if "@" not in email or "." not in email:
        return False
    if str(email).lower().endswith(GITHUB_NOREPLY_EMAIL_DOMAIN):
        return False
    return True


@handle_exceptions(default_return_value=None, raise_on_error=True)
def parse_subscription_object(
    subscription: stripe.ListObject[stripe.Subscription],
    installation_id: int,
    customer_id: str,
    owner_id: int,
    owner_name: str,
):
    """Parsing stripe subscription object to get the start date, end date, product id and interval"""
    if len(subscription.data) > 2:
        msg = "There are more than 2 active subscriptions for this customer. This is a check when we move to multiple paid subscriptions."
        logging.error(msg)
        raise ValueError(msg)

    free_tier_start_date = 0
    free_tier_end_date = 0
    free_tier_product_id = ""
    free_tier_interval = "month"  # Default interval

    # return the first paid subscription if found, if not return the free one found
    for sub in subscription.data:
        # Iterate over the items, there should only be one item, but we do this just in case
        for item in sub["items"]["data"]:
            # Check if item is non-free tier
            if item["price"]["id"] == STRIPE_FREE_TIER_PRICE_ID:
                # Save free tier info to return just in case paid tier is not found
                free_tier_start_date = sub.current_period_start
                free_tier_end_date = sub.current_period_end
                free_tier_product_id = item["price"]["product"]
                free_tier_interval = item["price"]["recurring"]["interval"]
                continue

            return (
                sub["current_period_start"],
                sub["current_period_end"],
                item["price"]["product"],
                item["price"]["recurring"]["interval"],
            )

    if (
        free_tier_start_date == 0
        or free_tier_end_date == 0
        or free_tier_product_id == ""
    ):
        # Customer should alawys have at least a free tier subscription, set by this codebase on installation webhook from github
        subscribe_to_free_plan(
            customer_id=customer_id,
            owner_id=owner_id,
            owner_name=owner_name,
            installation_id=installation_id,
        )
        subscription = get_subscription(customer_id=customer_id)
        return parse_subscription_object(
            subscription=subscription,
            installation_id=installation_id,
            customer_id=customer_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    # Return from Free Tier Subscription if there is no paid subscription object
    return (
        free_tier_start_date,
        free_tier_end_date,
        free_tier_product_id,
        free_tier_interval,
    )


@handle_exceptions(
    default_return_value=(1, 1, DEFAULT_TIME, False), raise_on_error=False
)
def get_how_many_requests_left_and_cycle(
    installation_id: int,
    owner_id: int,
    owner_name: str,
    owner_type: str = None,
    repo_name: str = None,
    issue_number: int = None,
):
    # Check if stripe customer id exists for installation
    data, _ = (
        supabase.table(table_name="installations")
        .select("owner_id, owners(stripe_customer_id)")
        .eq(column="installation_id", value=installation_id)
        .execute()
    )
    stripe_customer_id = (
        data[1][0].get("owners", {}).get("stripe_customer_id")
        if data and data[1] and data[1][0]
        else None
    )
    if not stripe_customer_id or not isinstance(stripe_customer_id, str):
        msg = f"No Stripe Customer ID found for installation {installation_id} owner {owner_id}. This has to do with fetching from Supabase."
        logging.error(msg)
        return (1, 1, DEFAULT_TIME, False)

    # Get subscription object and extract start date, end date and product id
    subscription = get_subscription(customer_id=stripe_customer_id)
    start_date_seconds, end_date_seconds, product_id, interval = (
        parse_subscription_object(
            subscription=subscription,
            installation_id=installation_id,
            customer_id=stripe_customer_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    )

    # Get base request count from product id metadata
    base_request_limit = get_base_request_limit(product_id)
    request_limit = (
        base_request_limit * 12 if interval == "year" else base_request_limit
    )
    start_date = datetime.fromtimestamp(timestamp=start_date_seconds, tz=TZ)
    end_date = datetime.fromtimestamp(timestamp=end_date_seconds, tz=TZ)

    # Get completed requests for this installation
    data, _ = (
        supabase.table("usage")
        .select("owner_type, owner_name, repo_name, issue_number")
        .gt("created_at", start_date)
        .eq("installation_id", installation_id)
        .eq("is_completed", True)
        .execute()
    )

    # Process unique requests in Python by combining fields
    unique_requests = {
        f"{record['owner_type']}/{record['owner_name']}/{record['repo_name']}#{record['issue_number']}"
        for record in data[1]
    }

    # Check if issue is already used
    is_retried = False
    if owner_type and repo_name and issue_number:
        current_request = f"{owner_type}/{owner_name}/{repo_name}#{issue_number}"
        is_retried = current_request in unique_requests
    print(f"is_retried: {is_retried}")

    requests_left = request_limit - len(unique_requests)
    print(f"requests_left: {requests_left}")
    return (requests_left, request_limit, end_date, is_retried)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_user(user_id: int):
    """Get user info from the users table"""
    data, _ = (
        supabase.table(table_name="users")
        .select("*")
        .eq(column="user_id", value=user_id)
        .execute()
    )
    if len(data[1]) > 0:
        user: dict[str, Any] = data[1][0]
        return user
    return None


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_user(user_id: int, user_name: str, email: str | None) -> None:
    # Check if email is valid
    email = email if check_email_is_valid(email=email) else None

    # Upsert user
    supabase.table(table_name="users").upsert(
        json={
            "user_id": user_id,
            "user_name": user_name,
            **({"email": email} if email else {}),
            "created_by": str(user_id),  # Because created_by is text
        },
        on_conflict="user_id",
    ).execute()
