from supabase import create_client, Client
import datetime


# Manager class to handle installation tokens
class InstallationTokenManager:
    # Initialize Supabase client when the manager is created
    def __init__(self, url, key):
        self.client: Client = create_client(url, key)

    # Save the installation token to the database
    def save_installation_token(self, installation_id, access_token, expires_in):
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
        data = {
            "installation_id": installation_id,
            "access_token": access_token,
            "expires_at": expires_at
        }
        self.client.table("installation_tokens").upsert(data).execute()
        return None

    # Get the installation token from the database
    def get_installation_token(self, installation_id):
        query = self.client.table("installation_tokens").select("access_token").eq("installation_id", installation_id)
        data = query.execute()
        if data.data and len(data.data) > 0:
            return data.data[0]['access_token']
        return None

    # Invalidate the installation token by setting it to an empty string
    def invalidate_installation_token(self, installation_id):
        data = {"access_token": ""}
        self.client.table("installation_tokens").update(data).eq("installation_id", installation_id).execute()

    # Delete the installation token from the database
    def delete_installation_token(self, installation_id):
        self.client.table("installation_tokens").delete().eq("installation_id", installation_id).execute()
