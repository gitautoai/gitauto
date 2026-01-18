from services.efs.cleanup_repo_efs import cleanup_repo_efs
from services.github.types.github_types import GitHubInstallationRepositoriesPayload
from services.supabase.installations.is_installation_valid import is_installation_valid
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_installation_repos_removed(payload: GitHubInstallationRepositoriesPayload):
    installation_id = payload["installation"]["id"]
    if not is_installation_valid(installation_id=installation_id):
        return

    owner_name = payload["installation"]["account"]["login"]

    for repo in payload["repositories_removed"]:
        repo_name = repo["name"]
        cleanup_repo_efs(owner=owner_name, repo=repo_name)
        logger.info(
            "Cleaned up EFS for removed repository: %s/%s", owner_name, repo_name
        )
