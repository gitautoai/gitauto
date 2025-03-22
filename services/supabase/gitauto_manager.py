"""Class to manage all GitAuto related operations"""

from datetime import datetime, timezone
from supabase import Client
from services.stripe.customer import create_stripe_customer, subscribe_to_free_plan
from services.supabase.users_manager import UsersManager
from utils.handle_exceptions import handle_exceptions


class GitAutoAgentManager:
    """Class to manage all GitAuto related operations"""

    def __init__(self, client: Client) -> None:
        self.client = client

    @handle_exceptions(default_return_value=None, raise_on_error=False)
    def complete_and_update_usage_record(
        self,
        usage_record_id: int,
        token_input: int,
        token_output: int,
        total_seconds: int,
        is_completed: bool = True,
    ) -> None:
        """Add agent information to usage record and set is_completed to True."""
        self.client.table(table_name="usage").update(
            json={
                "is_completed": is_completed,
                "token_input": token_input,
                "token_output": token_output,
                "total_seconds": total_seconds,
            }
        ).eq(column="id", value=usage_record_id).execute()

    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def create_installation(
        self,
        installation_id: int,
        owner_type: str,
        owner_name: str,
        owner_id: int,
        user_id: int,
        user_name: str,
        email: str | None,
    ) -> None:
        """Create owners record with stripe customerId, subscribe to free plan, create installation record, create users record on Installation Webhook event"""
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

        # Upsert user
        users_manager = UsersManager(client=self.client)
        users_manager.upsert_user(user_id=user_id, user_name=user_name, email=email)

    @handle_exceptions(default_return_value=None, raise_on_error=True)
    async def create_user_request(
        self,
        user_id: int,
        user_name: str,
        installation_id: int,
        unique_issue_id: str,
        email: str | None,
    ) -> int:
        """Creates record in usage table for this user and issue."""
        # If issue doesn't exist, create one
        data, _ = (
            self.client.table(table_name="issues")
            .select("*")
            .eq(column="unique_id", value=unique_issue_id)
            .execute()
        )

        # If no issue exists with that unique_issue_id, create one
        if not data[1]:
            self.client.table(table_name="issues").insert(
                json={"unique_id": unique_issue_id, "installation_id": installation_id}
            ).execute()

        # Add user request to usage table
        data, _ = (
            self.client.table(table_name="usage")
            .insert(
                json={
                    "user_id": user_id,
                    "installation_id": installation_id,
                    "unique_issue_id": unique_issue_id,
                }
            )
            .execute()
        )

        # Upsert user
        users_manager = UsersManager(client=self.client)
        users_manager.upsert_user(user_id=user_id, user_name=user_name, email=email)

        return data[1][0]["id"]

    @handle_exceptions(default_return_value=None, raise_on_error=False)
    def delete_installation(self, installation_id: int, user_id: int) -> None:
        """We don't cancel a subscription associated with this installation id since paid users sometimes mistakenly uninstall our app"""
        data = {
            "uninstalled_at": datetime.now(tz=timezone.utc).isoformat(),
            "uninstalled_by": user_id,
        }
        (
            self.client.table(table_name="installations")
            .update(json=data)
            .eq(column="installation_id", value=installation_id)
            .execute()
        )

    @handle_exceptions(default_return_value=None, raise_on_error=False)
    def get_installation_id(self, owner_id: int) -> int:
        """https://supabase.com/docs/reference/python/is"""
        data, _ = (
            self.client.table(table_name="installations")
            .select("installation_id")
            .eq(column="owner_id", value=owner_id)
            .is_(column="uninstalled_at", value="null")  # Not uninstalled
            .execute()
        )
        # Return the first installation id even if there are multiple installations
        return data[1][0]["installation_id"]

    @handle_exceptions(default_return_value=None, raise_on_error=False)
    def get_installation_ids(self) -> list[int]:
        """https://supabase.com/docs/reference/python/is"""
        data, _ = (
            self.client.table(table_name="installations")
            .select("installation_id")
            .is_(column="uninstalled_at", value="null")  # Not uninstalled
            .execute()
        )
        return [item["installation_id"] for item in data[1]]

    @handle_exceptions(default_return_value=False, raise_on_error=False)
    def is_users_first_issue(self, user_id: int, installation_id: int) -> bool:
        # Check if there are any completed usage records for this user and installation
        data, _ = (
            self.client.table(table_name="usage")
            .select("*")
            .eq(column="user_id", value=user_id)
            .eq(column="installation_id", value=installation_id)
            .eq(column="is_completed", value=True)
            .execute()
        )
        return len(data[1]) == 0

    @handle_exceptions(default_return_value=None, raise_on_error=False)
    def set_issue_to_merged(self, unique_issue_id: str) -> None:
        (
            self.client.table(table_name="issues")
            .update(json={"merged": True})
            .eq(column="unique_id", value=unique_issue_id)
            .execute()
        )
