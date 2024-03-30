"""Class to manage all GitAuto related operations"""

import datetime
import logging
from supabase import Client
from services.stripe.customer import create_stripe_customer, subscribe_to_free_plan


class GitAutoAgentManager:
    def __init__(self, client: Client) -> None:
        self.client = client

    def complete_user_request(self, user_id: int, installation_id: int) -> None:
        """Set users usage request to completed"""
        try:
            self.client.table(table_name="usage").update(
                json={
                    "is_completed": True,
                }
            ).eq(column="user_id", value=user_id).eq(
                column="installation_id", value=installation_id
            ).execute()
        except Exception as e:
            logging.error(
                msg=f"complete_user_request user_id {user_id} installation_id {installation_id} Error: {e}"
            )

    def create_installation(
        self,
        installation_id: int,
        owner_type: str,
        owner_name: str,
        owner_id: int,
        user_id: int,
        user_name: str,
    ) -> None:
        """Create owners record with stripe customerId, subscribe to free plan, create installation record, create users record on Installation Webhook event"""
        try:
            # If owner doesn't exist in owners table, insert owner and stripe customer
            data, _ = (
                self.client.table(table_name="owners")
                .select("owner_id")
                .eq(column="owner_id", value=owner_id)
                .execute()
            )
            if not data[1]:
                customer_id = create_stripe_customer(
                    owner_name=owner_name,
                    owner_id=owner_id,
                    installation_id=installation_id,
                    user_id=user_id,
                    user_name=user_name,
                )
                subscribe_to_free_plan(
                    customer_id=customer_id,
                    user_id=user_id,
                    user_name=user_name,
                    owner_id=owner_id,
                    owner_name=owner_name,
                    installation_id=installation_id,
                )
                self.client.table(table_name="owners").insert(
                    json={"owner_id": owner_id, "stripe_customer_id": customer_id}
                ).execute()

            # Insert installation record
            self.client.table(table_name="installations").insert(
                json={
                    "installation_id": installation_id,
                    "owner_name": owner_name,
                    "owner_type": owner_type,
                    "owner_id": owner_id,
                }
            ).execute()

            # Create User, and set is_selected to True if user has no selected account
            is_selected = True
            data, _ = (
                self.client.table(table_name="users")
                .select("user_id")
                .eq(column="user_id", value=user_id)
                .eq(column="is_selected", value=True)
                .execute()
            )
            if len(data[1]) > 0:
                is_selected = False
            self.client.table(table_name="users").insert(
                json={
                    "user_id": user_id,
                    "user_name": user_name,
                    "installation_id": installation_id,
                    "is_selected": is_selected,
                }
            ).execute()

        except Exception as e:
            logging.error(
                msg=f"create_installation installation_id: {installation_id} owner_id: {owner_id} Error: {e}"
            )

    def create_user_request(
        self, user_id: int, installation_id: int, unique_issue_id: str
    ) -> None:
        try:
            # If issue doesn't exist, create one
            data, _ = (
                self.client.table(table_name="issues")
                .select("progress")
                .eq(column="unique_id", value=unique_issue_id)
                .execute()
            )
            if not data[1]:
                self.client.table(table_name="issues").insert(
                    json={
                        "unique_id": unique_issue_id,
                        "progress": 100,
                        "installation_id": installation_id,
                    }
                ).execute()
            # Add user request to usage table
            self.client.table(table_name="usage").insert(
                json={
                    "user_id": user_id,
                    "installation_id": installation_id,
                    "unique_issue_id": unique_issue_id,
                }
            ).execute()
        except Exception as e:
            logging.error(
                msg=f"create_user_request user_id: {user_id} installation_id: {installation_id} Error: {e}"
            )

    def delete_installation(self, installation_id: int) -> None:
        """We don't cancel a subscription associated with this installation id since paid users sometimes mistakenly uninstall our app"""
        try:
            data: dict[str, str] = {
                "uninstalled_at": datetime.datetime.utcnow().isoformat()
            }
            self.client.table(table_name="installations").update(json=data).eq(
                column="installation_id", value=installation_id
            ).execute()
        except Exception as e:
            logging.error(
                msg=f"delete_installation installation_id: {installation_id} Error: {e}"
            )

    def is_issue_in_progress(self, unique_issue_id: str) -> bool:
        try:
            data, _ = (
                self.client.table(table_name="issues")
                .select("progress")
                .eq(column="unique_id", value=unique_issue_id)
                .execute()
            )
            if data[1][0]["progress"] == 100:
                return False
            return True
        except Exception as e:
            logging.error(msg=f"Start Progress Error: {e}")

    def is_users_first_issue(self, user_id: int, installation_id: int) -> bool:
        """Checks if it's the users first issue"""
        try:
            data, _ = (
                self.client.table(table_name="users")
                .select("*")
                .eq(column="user_id", value=user_id)
                .eq(column="installation_id", value=installation_id)
                .eq(column="first_issue", value=True)
                .execute()
            )
            if len(data[1]) > 0:
                return True
            return False
        except Exception as e:
            logging.error(msg=f"is_users_first_issue Error: {e}")

    def set_issue_to_merged(self, unique_issue_id: str) -> None:
        try:
            data, _ = (
                self.client.table(table_name="issues")
                .update(json={"merged": True})
                .eq(column="unique_id", value=unique_issue_id)
                .execute()
            )
        except Exception as e:
            logging.error(msg=f"set_issue_to_merged Error: {e}")

    def set_user_first_issue_to_false(self, user_id: int, installation_id: int) -> None:
        try:
            data, _ = (
                self.client.table(table_name="users")
                .update(json={"first_issue": False})
                .eq(column="user_id", value=user_id)
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
        except Exception as e:
            logging.error(msg=f"Increment Request Count Error: {e}")

    def update_progress(self, unique_issue_id: str, progress: int) -> None:
        """Update the progress of generating the PR in a comment of the issue."""
        try:
            self.client.table(table_name="issues").update(
                json={"progress": progress}
            ).eq(column="unique_id", value=unique_issue_id).execute()
        except Exception as e:
            logging.error(msg=f"Update Progress Error: {e}")
