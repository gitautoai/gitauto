# Standard imports
import json
import os

# Local imports
from payloads.aws.setup_installed_repository_event import SetupInstalledRepositoryEvent
from schemas.supabase.types import OwnerType
from services.aws.clients import lambda_client
from services.github.types.repository import RepositoryAddedOrRemoved
from services.webhook.setup_installed_repository import setup_installed_repository
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
def process_repositories(
    owner_id: int,
    owner_name: str,
    owner_type: OwnerType,
    repositories: list[RepositoryAddedOrRemoved],
    user_id: int,
    user_name: str,
    installation_id: int,
    sender_email: str | None,
    sender_display_name: str,
):
    # AWS_LAMBDA_FUNCTION_NAME is automatically set by AWS Lambda runtime
    lambda_function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")

    # On Lambda: invoke a separate Lambda per repo (parallel, async fire-and-forget)
    if lambda_function_name:
        for repo in repositories:
            payload: SetupInstalledRepositoryEvent = {
                "triggerType": "setup_installed_repository",
                "owner_id": owner_id,
                "owner_name": owner_name,
                "owner_type": owner_type,
                "repo_id": repo["id"],
                "repo_name": repo["name"],
                "installation_id": installation_id,
                "user_id": user_id,
                "user_name": user_name,
                "sender_email": sender_email,
                "sender_display_name": sender_display_name,
            }
            logger.info("Dispatching Lambda for %s/%s", owner_name, repo["name"])
            lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType="Event",
                Payload=json.dumps(payload),
            )
        logger.info(
            "Dispatched %d Lambda invocations for %s", len(repositories), owner_name
        )
        return

    # Local dev: process sequentially (no Lambda self-invocation)
    for repo in repositories:
        setup_installed_repository(
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_id=repo["id"],
            repo_name=repo["name"],
            installation_id=installation_id,
            user_id=user_id,
            user_name=user_name,
            sender_email=sender_email,
            sender_display_name=sender_display_name,
        )
