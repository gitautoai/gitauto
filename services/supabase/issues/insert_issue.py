from schemas.supabase.fastapi.schema_public_latest import IssuesInsert
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def insert_issue(
    owner_id: int,
    owner_type: str,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    issue_number: int,
    installation_id: int,
):
    issue_data = IssuesInsert(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        issue_number=issue_number,
        installation_id=installation_id,
    )
    supabase.table(table_name="issues").insert(json=issue_data.model_dump()).execute()
