from schemas.supabase.fastapi.schema_public_latest import RepositoriesUpdate
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_repository(
    repo_id: int,
    user_id: int,
    user_name: str,
    file_count: int,
    blank_lines: int,
    comment_lines: int,
    code_lines: int,
):
    repository_data = RepositoriesUpdate(
        file_count=file_count,
        blank_lines=blank_lines,
        comment_lines=comment_lines,
        code_lines=code_lines,
        updated_by=str(user_id) + ":" + user_name,
    )
    repository_data_dict = repository_data.model_dump(exclude_none=True)
    update_result = (
        supabase.table("repositories")
        .update(repository_data_dict)
        .eq("repo_id", repo_id)
        .execute()
    )
    return update_result.data[0] if update_result.data else None
