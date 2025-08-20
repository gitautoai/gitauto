# Standard imports
import os

# Local imports
from services.aws.clients import lambda_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def switch_lambda_log_group(owner_name: str, repo_name: str):
    """Switch Lambda function to use repo-specific log group."""
    function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "pr-agent-prod")
    repo_log_group = f"/aws/lambda/gitauto/{owner_name}/{repo_name}"

    lambda_client.update_function_configuration(
        FunctionName=function_name, LoggingConfig={"LogGroup": repo_log_group}
    )
