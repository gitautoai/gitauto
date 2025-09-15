from typing import Any
from fastapi import Request
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def extract_lambda_info(request: Request):
    """
    Extract Lambda context information from FastAPI request scope.

    Returns a dictionary with:
    - log_group: CloudWatch log group name. E.g. "/aws/lambda/pr-agent-prod"
    - log_stream: CloudWatch log stream name. E.g. "2025/09/04/pr-agent-prod[$LATEST]841315c5"
    - request_id: AWS request ID for this Lambda invocation. E.g. "17921070-5cb6-43ee-8d2e-b5161ae89729"
    """
    lambda_info: dict[str, str | None] = {}

    if "aws" in request.scope:
        aws_scope: dict[str, Any] = request.scope["aws"]
        if "context" in aws_scope:
            aws_context = aws_scope["context"]
            lambda_info = {
                "log_group": getattr(aws_context, "log_group_name", None),
                "log_stream": getattr(aws_context, "log_stream_name", None),
                "request_id": getattr(aws_context, "aws_request_id", None),
            }

    return lambda_info
