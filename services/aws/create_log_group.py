# Local imports
from services.aws.clients import logs_client
from services.aws.constants import LAMBDA_LOG_GROUP_BASE
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_log_group(owner_name: str, repo_name: str):
    """Create CloudWatch log group."""
    log_group_name = f"{LAMBDA_LOG_GROUP_BASE}/{owner_name}/{repo_name}"
    try:
        logs_client.create_log_group(logGroupName=log_group_name)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        # Skip error notification if log group already exists
        pass
