import datetime
from supabase import create_client, Client
import logging

# Manager class to handle installation tokens
class InstallationTokenManager:
    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(supabase_url=url, supabase_key=key)

    def save_installation_token(
            self, installation_id: int, owner_name: str
            ) -> None:
        data, _ = self.client.table(table_name="owner_info").select("*").eq(column="installation_id", value=installation_id).execute()
        if (len(data[1]) > 0):
            self.client.table(table_name="owner_info").update(json={
                "installation_id": installation_id,
                "owner_name": owner_name,
                "deleted_at": None,
            }).eq(column="installation_id", value=installation_id).execute()
        else:
            self.client.table(table_name="owner_info").insert(json={
                "installation_id": installation_id,
                "owner_name": owner_name,
            }).execute()


    def delete_installation_token(self, installation_id: int) -> None:
        data: dict[str, str] = {"deleted_at": datetime.datetime.utcnow().isoformat()}
        self.client.table(table_name="owner_info").update(json=data).eq(column="installation_id", value=installation_id).execute()
        
    def increment_request_count(self, installation_id: int) -> None:
        try: 
            data, _ = self.client.table(table_name="owner_info").select("request_count").eq(column="installation_id", value=installation_id).execute()
            print(data)
            if (data[1] and data[1][0]):
                self.client.table(table_name="owner_info").update(json={"request_count": data[1][0]['request_count'] + 1}).eq(column="installation_id", value=installation_id).execute()
        except Exception as e:
            logging.error(msg=f"Increment Request Count Error: {e}")
    
    def increment_completed_count(self, installation_id: int) -> None:
        try: 
            data, _ = self.client.table(table_name="owner_info").select("completed_request_count").eq(column="installation_id", value=installation_id).execute()
            if (data[1] and data[1][0]):
                self.client.table(table_name="owner_info").update(json={"completed_request_count": data[1][0]['completed_request_count'] + 1}).eq(column="installation_id", value=installation_id).execute()
        except Exception as e:
            logging.error(msg=f"Increment Completed Issues Count Error: {e}")
            
            
    def start_progress(self, unique_issue_id: str, installation_id: int) -> bool:
        try: 
            data, _ = self.client.table(table_name="issues").select("progress").eq(column="unique_id", value=unique_issue_id).execute()
            if(len(data[1]) == 0):
                self.client.table(table_name="issues").insert(json={
                    "unique_id": unique_issue_id,
                    "progress": 0,
                    "installation_id": installation_id,
                }).execute()
                return False
            elif( data[1][0]['progress'] == 100):
                return False
            else: 
                return True
        except Exception as e:
            logging.error(msg=f"Start Progress Error: {e}")
            
            
    def update_progress(self,unique_issue_id: str, progress: int) -> None:
        try: 
            self.client.table(table_name="issues").update(json={"progress": progress}).eq(column="unique_id", value=unique_issue_id).execute()
            # Update progress on issue
        except Exception as e:
            logging.error(msg=f"Update Progress Error: {e}")
            
    def finish_progress(self, unique_issue_id: str) -> None:
        try: 
            self.client.table(table_name="issues").update(json={"progress": 100}).eq(column="unique_id", value=unique_issue_id).execute()
            # update progress on issue
        except Exception as e:
            logging.error(msg=f"Finish Progress Error: {e}")