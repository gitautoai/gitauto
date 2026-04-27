# Local imports
from schemas.supabase.types import OwnerType
from services.supabase.owners.insert_owner import insert_owner
from services.supabase.owners.get_owner import get_owner
from services.supabase.repositories.get_repository import get_repository
from services.supabase.repositories.insert_repository import insert_repository
from services.supabase.repositories.update_repository import update_repository
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_repository(
    *,
    platform: Platform,
    owner_id: int,
    owner_name: str,
    owner_type: OwnerType,
    repo_id: int,
    repo_name: str,
    user_id: int,
    user_name: str,
    file_count: int = 0,
    code_lines: int = 0,
):
    # First check if owner exists since it's a foreign key
    owner = get_owner(platform=platform, owner_id=owner_id)

    # If owner doesn't exist, create it (without stripe_customer_id - will be added later)
    if not owner:
        logger.info("upsert_repository: owner %s missing, inserting", owner_id)
        insert_owner(
            platform=platform,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            user_id=user_id,
            user_name=user_name,
            stripe_customer_id="",
        )

    # Check if repository already exists
    repository = get_repository(platform=platform, owner_id=owner_id, repo_id=repo_id)

    if repository:
        logger.info("upsert_repository: existing repo %s, updating", repo_id)
        # Update existing repository - only include stats if non-zero
        kwargs = {}
        if file_count:
            logger.info("upsert_repository: updating file_count=%s", file_count)
            kwargs["file_count"] = file_count
        if code_lines:
            logger.info("upsert_repository: updating code_lines=%s", code_lines)
            kwargs["code_lines"] = code_lines
        return update_repository(
            platform=platform,
            owner_id=owner_id,
            repo_id=repo_id,
            updated_by=f"{user_id}:{user_name}",
            **kwargs,
        )

    # Create new repository
    logger.info("upsert_repository: new repo %s, inserting", repo_id)
    return insert_repository(
        platform=platform,
        owner_id=owner_id,
        repo_id=repo_id,
        repo_name=repo_name,
        user_id=user_id,
        user_name=user_name,
        file_count=file_count,
        code_lines=code_lines,
    )
