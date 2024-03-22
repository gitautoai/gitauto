import datetime
from supabase import create_client, Client
import logging


# Manager class to handle installation tokens
class InstallationTokenManager:
    def __init__(self, client: Client) -> None:
        self.client = client

    def save_installation_token(
        self, installation_id: int, owner_type: str, owner_name: str
    ) -> None:
        data, _ = (
            self.client.table(table_name="owner_info")
            .select("*")
            .eq(column="owner_name", value=owner_name)
            .execute()
        )
        if len(data[1]) > 0:
            self.client.table(table_name="owner_info").update(
                json={
                    "installation_id": installation_id,
                    "owner_name": owner_name,
                    "owner_type": owner_type,
                    "deleted_at": None,
                }
            ).eq(column="owner_name", value=owner_name).execute()
        else:
            self.client.table(table_name="owner_info").insert(
                json={
                    "installation_id": installation_id,
                    "owner_name": owner_name,
                    "owner_type": owner_type,
                }
            ).execute()

    def delete_installation_token(self, installation_id: int) -> None:
        data: dict[str, str] = {"deleted_at": datetime.datetime.utcnow().isoformat()}
        self.client.table(table_name="owner_info").update(json=data).eq(
            column="installation_id", value=installation_id
        ).execute()

    def increment_request_count(self, installation_id: int) -> None:
        try:
            data, _ = (
                self.client.table(table_name="owner_info")
                .select("request_count")
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            if data[1] and data[1][0]:
                self.client.table(table_name="owner_info").update(
                    json={"request_count": data[1][0]["request_count"] + 1}
                ).eq(column="installation_id", value=installation_id).execute()
        except Exception as e:
            logging.error(msg=f"increment_request_count Error: {e}")

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

    def increment_completed_count(self, installation_id: int) -> None:
        try:
            data, _ = (
                self.client.table(table_name="owner_info")
                .select("completed_request_count")
                .eq(column="installation_id", value=installation_id)
                .execute()
            )
            if data[1] and data[1][0]:
                self.client.table(table_name="owner_info").update(
                    json={
                        "completed_request_count": data[1][0]["completed_request_count"]
                        + 1
                    }
                ).eq(column="installation_id", value=installation_id).execute()
        except Exception as e:
            logging.error(msg=f"increment_completed_count Error: {e}")

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

    def save_progress_started(self, unique_issue_id: str, installation_id: int) -> bool:
        try:
            print("INSTALL ID: ", installation_id)
            print("UID", unique_issue_id)
            data, _ = (
                self.client.table(table_name="issues")
                .select("progress")
                .eq(column="unique_id", value=unique_issue_id)
                .execute()
            )
            print(data)
            if len(data[1]) == 0:
                self.client.table(table_name="issues").insert(
                    json={
                        "unique_id": unique_issue_id,
                        "progress": 0,
                        "installation_id": installation_id,
                    }
                ).execute()
                return True
            elif data[1][0]["progress"] == 100:
                return True
            else:
                return False
        except Exception as e:
            logging.error(msg=f"Start Progress Error: {e}")

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
