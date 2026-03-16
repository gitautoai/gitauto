from dataclasses import dataclass

from services.efs.get_efs_dir import get_efs_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import git_clone_to_efs
from services.git.get_default_branch import get_default_branch
from services.github.token.get_installation_token import get_installation_access_token
from services.node.ensure_node_packages import ensure_node_packages
from services.php.ensure_php_packages import ensure_php_packages
from services.supabase.installations.get_installation_by_owner import (
    get_installation_by_owner,
)
from services.supabase.repositories.get_repository_by_name import get_repository_by_name
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger, set_owner_repo, set_trigger


@dataclass
class CloneAndInstallResult:
    status: str
    message: str
    efs_dir: str
    node_installed: bool
    php_installed: bool


@handle_exceptions(default_return_value=None, raise_on_error=False)
def clone_and_install(owner: str, repo: str):
    set_owner_repo(owner, repo)
    set_trigger("clone_and_install")
    logger.info("Starting clone_and_install for %s/%s", owner, repo)

    installation = get_installation_by_owner(owner)
    if not installation:
        logger.warning("No installation found for %s", owner)
        return CloneAndInstallResult(
            status="error",
            message=f"No installation found for {owner}",
            efs_dir="",
            node_installed=False,
            php_installed=False,
        )

    installation_id = installation["installation_id"]
    owner_id = installation["owner_id"]
    token = get_installation_access_token(installation_id)

    repository = get_repository_by_name(owner_id, repo)
    if repository and repository.get("target_branch"):
        branch = repository["target_branch"]
        logger.info("Using target_branch from repository: %s", branch)
    else:
        clone_url = get_clone_url(owner, repo, token)
        branch = get_default_branch(clone_url=clone_url)
        if not branch:
            logger.warning("Repository %s/%s is empty", owner, repo)
            return CloneAndInstallResult(
                status="error",
                message="Repository is empty",
                efs_dir="",
                node_installed=False,
                php_installed=False,
            )
        logger.info("Using default branch: %s", branch)

    efs_dir = get_efs_dir(owner, repo)
    clone_url = get_clone_url(owner, repo, token)

    logger.info("Cloning to EFS: %s", efs_dir)
    git_clone_to_efs(efs_dir, clone_url, branch)

    logger.info("Installing node packages")
    node_result = ensure_node_packages(owner_id=owner_id, efs_dir=efs_dir)
    logger.info("node: ready=%s", node_result)

    logger.info("Installing PHP packages")
    php_result = ensure_php_packages(owner_id=owner_id, efs_dir=efs_dir)
    logger.info("php: ready=%s", php_result)

    logger.info("Clone and install completed for %s/%s", owner, repo)
    return CloneAndInstallResult(
        status="success",
        message="",
        efs_dir=efs_dir,
        node_installed=node_result,
        php_installed=php_result,
    )
