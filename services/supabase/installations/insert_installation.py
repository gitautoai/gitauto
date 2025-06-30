from schemas.supabase.fastapi.schema_public_latest import InstallationsInsert
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def insert_installation(
    installation_id: int,
    owner_id: int,
    owner_type: str,
    owner_name: str,
):
    installation_data = InstallationsInsert(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
    )
    installation_data_dict = installation_data.model_dump(exclude_none=True)
    supabase.table(table_name="installations").insert(
        json=installation_data_dict
    ).execute()
