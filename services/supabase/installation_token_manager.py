import datetime
import logging

from supabase import Client


# Manager class to handle installation tokens
class InstallationTokenManager:
    def __init__(self, client: Client) -> None:
        self.client = client

    def complete_user_request(self, user_id: int, installation_id: int) -> None:
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
        self, installation_id: int, owner_type: str, owner_name: str, owner_id: int
    ) -> None:
        try:
            # If owner doesn't exist in owner_info table, insert owner record
            data, _ = (
                self.client.table(table_name="owner_info_table")
                .select("owner_id")
                .eq(column="owner_id", value=owner_id)
                .execute()
            )
            if not data[1]:
                self.client.table(table_name="owner_info_table").insert(
                    json={"owner_id": owner_id}
                ).execute()

            # Insert installation record
            self.client.table(table_name="owner_info").insert(
                json={
                    "installation_id": installation_id,
                    "owner_name": owner_name,
                    "owner_type": owner_type,
                    "owner_id": owner_id,
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
        data: dict[str, str] = {
            "uninstalled_at": datetime.datetime.utcnow().isoformat()
        }
        self.client.table(table_name="owner_info").update(json=data).eq(
            column="installation_id", value=installation_id
        ).execute()

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

    def is_users_first_issue(self, installation_id: int) -> bool:
        """Checks if it's the users first issue"""
        try:
            data, _ = (
                self.client.table(table_name="owner_info")
                .select("first_issue")
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            if data[1] and data[1][0]["first_issue"]:
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

    def set_user_first_issue_to_false(self, installation_id: int) -> None:
        # TODO change this first login to false on a user and not owner
        try:
            data, _ = (
                self.client.table(table_name="owner_info")
                .update(json={"first_issue": False})
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
