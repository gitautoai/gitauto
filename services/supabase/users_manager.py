"""Manager for all user related operations"""

from supabase import Client
import datetime
import logging
from services.stripe.customer import (
    get_subscription,
    get_request_count_from_product_id_metadata,
    subscribe_to_free_plan,
)
from config import (
    STRIPE_FREE_TIER_PRICE_ID,
)

import stripe


class UsersManager:
    """Manager for all user related operations"""

    def __init__(self, client: Client) -> None:
        self.client: Client = client

    def create_user(self, user_id: int, user_name: str, installation_id: int) -> None:
        """Creates an account for the user in the users table"""
        try:
            self.client.table(table_name="users").insert(
                json={
                    "user_id": user_id,
                    "user_name": user_name,
                    "installation_id": installation_id,
                }
            ).execute()
        except Exception as err:
            logging.error("create_user %s", err)

    # Check if user has a seat in an org or can be given a seat
    def is_user_eligible_for_seat_handler(
        self, user_id: int, installation_id: int, quantity: int
    ) -> bool:
        try:
            # Check is user already assigned to a seat
            data, _ = (
                self.client.table(table_name="users")
                .select("*")
                .eq(column="user_id", value=user_id)
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            if data[1][0]["is_user_assigned"]:
                return True
            else:
                # Check if a seat is available for a user
                assigned_users, _ = (
                    self.client.table(table_name="users")
                    .select("*")
                    .eq(column="installation_id", value=installation_id)
                    .eq(column="is_user_assigned", value=True)
                    .execute()
                )
                if len(assigned_users[1]) >= quantity:
                    return False
                else:
                    # Set user as assigned in db
                    self.client.table(table_name="users").update(
                        json={"is_user_assigned": True}
                    ).eq(column="user_id", value=user_id).eq(
                        column="installation_id", value=installation_id
                    ).execute()
            return True
        except Exception as err:
            logging.error(f"is_user_eligible_for_seat_handler {err}")
            # Give user a seat even if there is an error
            return True

    def parse_subscription_object(
        self,
        subscription: stripe.ListObject[stripe.Subscription],
        user_id: int,
        installation_id: int,
        customer_id: str,
        user_name: str,
        owner_id: int,
        owner_name: str,
    ) -> tuple[int, int, str]:
        """Parsing stripe subscription object to get the start date, end date and product id of either a paid or free tier customer subscription"""
        try:
            if len(subscription.data) > 2:
                raise ValueError(
                    "There are more than 2 active subscriptions for this customer. This is a check when we move to multiple paid subscriptions."
                )

            free_tier_start_date = 0
            free_tier_end_date = 0
            free_tier_product_id = ""
            # return the first paid subscription if found, if not return the free one found
            for sub in subscription.data:
                # Iterate over the items, there should only be one item, but we are iterating just in case
                for item in sub["items"]["data"]:
                    # Check if item is non-free tier
                    if item["price"]["id"] == STRIPE_FREE_TIER_PRICE_ID:
                        # Save free tier info to return just in case paid tier is not found
                        free_tier_start_date = sub.current_period_start
                        free_tier_end_date = sub.current_period_end
                        free_tier_product_id = item["price"]["product"]
                        continue

                    # Check if user has or can be assigned a seat
                    if self.is_user_eligible_for_seat_handler(
                        user_id=user_id,
                        installation_id=installation_id,
                        quantity=item["quantity"],
                    ):
                        return (
                            sub["current_period_start"],
                            sub["current_period_end"],
                            item["price"]["product"],
                        )

            if (
                free_tier_start_date == 0
                or free_tier_end_date == 0
                or free_tier_product_id == ""
            ):
                # Customer should alawys have at least a free tier subscription, set by this codebase on installation webhook from github
                subscribe_to_free_plan(
                    customer_id=customer_id,
                    user_id=user_id,
                    user_name=user_name,
                    owner_id=owner_id,
                    owner_name=owner_name,
                    installation_id=installation_id,
                )
                subscription = get_subscription(
                    customer_id=customer_id,
                )
                return self.parse_subscription_object(
                    subscription=subscription,
                    user_id=user_id,
                    installation_id=installation_id,
                    customer_id=customer_id,
                    user_name=user_name,
                    owner_id=owner_id,
                    owner_name=owner_name,
                )
            # Return from Free Tier Subscription if there is no paid subscription object
            return free_tier_start_date, free_tier_end_date, free_tier_product_id
        except Exception as e:
            logging.error(f"parse_subscription_object {e}")
            raise

    def get_how_many_requests_left_and_cycle(
        self,
        user_id: int,
        installation_id: int,
        user_name: str,
        owner_id: int,
        owner_name: str,
    ) -> tuple[int, int, datetime.datetime]:
        try:
            data, _ = (
                self.client.table(table_name="installations")
                .select("owner_id, owners(stripe_customer_id)")
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            stripe_customer_id: str = data[1][0]["owners"]["stripe_customer_id"]
            if stripe_customer_id:
                subscription = get_subscription(
                    customer_id=stripe_customer_id,
                )

                start_date_seconds, end_date_seconds, product_id = (
                    self.parse_subscription_object(
                        subscription=subscription,
                        user_id=user_id,
                        installation_id=installation_id,
                        customer_id=stripe_customer_id,
                        user_name=user_name,
                        owner_id=owner_id,
                        owner_name=owner_name,
                    )
                )

                request_count = get_request_count_from_product_id_metadata(product_id)

                start_date = datetime.datetime.fromtimestamp(start_date_seconds)
                end_date = datetime.datetime.fromtimestamp(end_date_seconds)

                # Calculate how many completed requests for this user account
                data, _ = (
                    self.client.table("usage")
                    .select("*")
                    .gt("created_at", start_date)
                    .eq("user_id", user_id)
                    .eq("installation_id", installation_id)
                    .eq("is_completed ", True)
                    .execute()
                )
                requests_left = request_count - len(data[1])

                return (
                    requests_left,
                    request_count,
                    end_date,
                )

            logging.error(
                "No Stripe Customer ID found for installation %s user %s",
                installation_id,
                user_id,
            )
            raise
        except Exception as err:
            logging.error(f"get_how_many_requests_left_and_cycle {err}")
            # Send back valid values and do not raise to give user benefit of the doubt
            return (
                1,
                1,
                datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=0),
            )

    def user_exists(self, user_id: int, installation_id: int) -> bool:
        """Check if user(installation_id, user_id) exists in GitAuto database"""
        try:
            data, _ = (
                self.client.table(table_name="users")
                .select("*")
                .eq(column="user_id", value=user_id)
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            if len(data[1]) > 0:
                return True
            return False
        except Exception as err:
            logging.error(f"user_exists {err}")
            return False
