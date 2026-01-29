from services.efs.get_efs_dir import get_efs_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import git_clone_to_efs
from services.github.branches.get_default_branch import get_default_branch
from services.github.token.get_installation_token import get_installation_access_token
from services.node.install_node_packages import install_node_packages
from services.supabase.installations.get_installation_by_owner import (
    get_installation_by_owner,
)
from services.supabase.repositories.get_repository_by_name import get_repository_by_name
from services.website.verify_api_key import verify_api_key
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger, set_owner_repo, set_trigger


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def clone_and_install(owner: str, repo: str, api_key: str):
    verify_api_key(api_key)
    set_owner_repo(owner, repo)
    set_trigger("clone_and_install")
    logger.info("Starting clone_and_install for %s/%s", owner, repo)

    installation = get_installation_by_owner(owner)
    if not installation:
        logger.warning("No installation found for %s", owner)
        return {"status": "error", "message": f"No installation found for {owner}"}

    installation_id = installation["installation_id"]
    owner_id = installation["owner_id"]
    token = get_installation_access_token(installation_id)

    repository = get_repository_by_name(owner_id, repo)
    if repository and repository.get("target_branch"):
        branch = repository["target_branch"]
        logger.info("Using target_branch from repository: %s", branch)
    else:
        branch, is_empty = get_default_branch(owner=owner, repo=repo, token=token)
        if is_empty:
            logger.warning("Repository %s/%s is empty", owner, repo)
            return {"status": "error", "message": "Repository is empty"}
        logger.info("Using default branch: %s", branch)

    efs_dir = get_efs_dir(owner, repo)
    clone_url = get_clone_url(owner, repo, token)

    logger.info("Cloning to EFS: %s", efs_dir)
    await git_clone_to_efs(efs_dir, clone_url, branch)

    logger.info("Installing node packages")
    result = await install_node_packages(
        owner=owner,
        owner_id=owner_id,
        repo=repo,
        branch=branch,
        token=token,
        efs_dir=efs_dir,
        timeout=840,  # 14 min (Lambda max is 15 min)
    )

    logger.info("Clone and install completed for %s/%s", owner, repo)
    return {"status": "success", "efs_dir": efs_dir, "installed": result}
