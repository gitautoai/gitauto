import datetime
import re
import time
from supabase import Client
import logging
from services.stripe.customer import (
    get_subscription,
    get_request_count_from_product_id_metadata,
)
from config import FREE_TIER_REQUEST_AMOUNT, STRIPE_FREE_TIER_PRICE_ID


class UsersManager:
    def __init__(self, client: Client) -> None:
        self.client = client

    def create_user(self, user_id: int, user_name: str, installation_id: int) -> None:
        try:
            self.client.table(table_name="users").insert(
                json={
                    "user_id": user_id,
                    "user_name": user_name,
                    "installation_id": installation_id,
                }
            ).execute()
        except Exception as err:
            logging.error(f"create_user {err}")

    def get_data_from_subscription_object(
        self, subscription, user_id: int, installation_id: int
    ):
        try:
            # Only one subscription, should be free tier
            if len(subscription["data"]) == 0:
                return subscription["data"][0]

            for sub in subscription["data"]:
                if sub["items"]["data"][0].price.id != STRIPE_FREE_TIER_PRICE_ID:
                    # Check if this user is eligible/has a seat in this subscription
                    if self.user_eligible_for_seat_handler(
                        user_id=user_id,
                        installation_id=installation_id,
                        quantity=sub["items"]["data"][0].quantity,
                    ):
                        return sub
                    else:
                        return subscription["data"][0]
            logging.error(
                f"get_current_period_from_subscription_object: No non-free tier found for userId {user_id} installationId {installation_id}"
            )
            return subscription["data"][0]
        except Exception as e:
            logging.error(f"get_current_period_from_subscription_object {e}")

    def get_how_many_requests_left_and_cycle(
        self, user_id: int, installation_id: int
    ) -> tuple[int, str]:
        try:
            data, _ = (
                self.client.table(table_name="installations")
                .select("owner_id, owners(stripe_customer_id)")
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            stripe_customer_id = data[1][0]["owners"]["stripe_customer_id"]

            if stripe_customer_id:
                subscription = get_subscription(
                    customer_id=stripe_customer_id,
                )
                subscription_data = self.get_data_from_subscription_object(
                    subscription=subscription,
                    user_id=user_id,
                    installation_id=installation_id,
                )

                start_date_seconds = subscription_data["current_period_start"]
                request_count = get_request_count_from_product_id_metadata(
                    subscription_data["items"]["data"][0]["price"]["product"]
                )

                start_date = datetime.datetime.fromtimestamp(start_date_seconds)

                data, _ = (
                    self.client.table("usage")
                    .select("*")
                    .gt("created_at", start_date)
                    .execute()
                )
                requests_left = request_count - len(data[1])
                end_date = (start_date + datetime.timedelta(days=30)).strftime(
                    "%m-%d-%Y"
                )
                return requests_left, end_date

            else:
                logging.error(
                    "No Stripe Customer ID found for installation %s user %s",
                    installation_id,
                    user_id,
                )

            return FREE_TIER_REQUEST_AMOUNT, "N/A"
        except Exception as err:
            logging.error(f"get_how_many_requests_left {err}")
            return -1

    def is_users_first_issue(self, user_id: int, installation_id: int) -> bool:
        try:
            data, _ = (
                self.client.table(table_name="users")
                .select("*")
                .eq(column="user_id", value=user_id)
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            print("DATA: ", data[1][0]["first_issue"])
            return True
            return data[1][0]["first_issue"]
        except Exception as err:
            logging.error(f"is_users_first_issue {err}")
            return True

    def user_eligible_for_seat_handler(
        self, user_id: int, installation_id: int, quantity: int
    ) -> bool:
        try:
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
                users, _ = (
                    self.client.table(table_name="users")
                    .select("*")
                    .eq(column="user_id", value=user_id)
                    .eq(column="installation_id", value=installation_id)
                    .execute()
                )
                if len(users[1]) >= quantity:
                    return False
                else:
                    self.client.table(table_name="users").update(
                        json={"is_user_assigned": True}
                    ).eq(column="user_id", value=user_id).eq(
                        column="installation_id", value=installation_id
                    ).execute()
        except Exception as err:
            logging.error(f"is_users_first_issue {err}")
            return True

    def user_exists(self, user_id: int, installation_id: int) -> None:
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
