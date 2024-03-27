import datetime
import re
from supabase import create_client, Client
import logging
from services.stripe.customer import get_subscription


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

    def get_how_many_requests_left(self, user_id: int, installation_id: int) -> int:
        try:
            data, _ = (
                self.client.table(table_name="installations")
                .select("owner_id, owners(stripe_customer_id)")
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            stripe_customer_id = data[1][0]["owners"]["stripe_customer_id"]
            print("STRIPE: ", stripe_customer_id)
            has_billing_cycle = False
            if stripe_customer_id:
                if get_subscription(stripe_customer_id) != -1:
                    has_billing_cycle = True
                    # TODO parse the billing cycle from stripe
            if not has_billing_cycle:
                first_request, _ = (
                    self.client.table("usage")
                    .select("created_at")
                    # .order_by("created_at", ascending=True)
                    .eq(column="user_id", value=user_id)
                    .eq(column="installation_id", value=installation_id)
                    .limit(1)
                    .execute()
                )
                return 5
                # TODO Find total requests in past month
                # day_of_week = re.search(
                #     r"\d{4}-\d{2}-(\d{2})", first_request[1][0]["created_at"]
                # ).group(1)

                # now = datetime.now()
                # last_month = now.replace(day=1) - timedelta(days=1)
                # last_month_start = last_month.replace(day=1)
                # last_month_end = last_month.replace(day=last_month.day)

                # total_requests, _ = (
                #     self.client.table(table_name="users")
                #     .select("id, usage(surrogate_user_id)")
                #     .eq(column="user_id", value=user_id)
                #     .eq(column="installation_id", value=installation_id)
                #     .execute()
                # )
                # print(total_requests)
                # return 5 - total_requests

            return 5
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
