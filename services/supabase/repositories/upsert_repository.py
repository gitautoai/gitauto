# Local imports
from services.supabase.owners.create_owner import create_owner
from services.supabase.owners.get_owner import get_owner
from services.supabase.repositories.get_repository import get_repository
from services.supabase.repositories.insert_repository import insert_repository
from services.supabase.repositories.update_repository import update_repository
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_repository(
    owner_id: int,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    user_id: int,
    user_name: str,
    file_count: int = 0,
    blank_lines: int = 0,
    comment_lines: int = 0,
    code_lines: int = 0,
):
    # First check if owner exists since it's a foreign key
    owner = get_owner(owner_id)

    # If owner doesn't exist, create it
    if not owner:
        create_owner(
            owner_id=owner_id,
            owner_name=owner_name,
            user_id=user_id,
            user_name=user_name,
        )

    # Check if repository already exists
    repository = get_repository(owner_id=owner_id, repo_id=repo_id)

    if repository:
        # Update existing repository
        return update_repository(
            owner_id=owner_id,
            repo_id=repo_id,
            updated_by=f"{user_id}:{user_name}",
            file_count=file_count,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            code_lines=code_lines,
        )

    # Create new repository
    return insert_repository(
        owner_id=owner_id,
        repo_id=repo_id,
        repo_name=repo_name,
        user_id=user_id,
        user_name=user_name,
        file_count=file_count,
        blank_lines=blank_lines,
        comment_lines=comment_lines,
        code_lines=code_lines,
    )
