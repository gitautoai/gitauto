import logging
from typing import Any
from fastapi import Request
from payloads.aws.lambda_types import LambdaContext
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def extract_lambda_info(request: Request):
    logging.info("Request scope: %s", request.scope)
    lambda_info: dict[str, str | None] = {}

    if "aws" in request.scope:
        aws_scope: dict[str, Any] = request.scope["aws"]
        logging.info("AWS scope: %s", aws_scope)
        if "context" in aws_scope:
            aws_context: LambdaContext = aws_scope["context"]
            logging.info("Lambda context: %s", aws_context)
            lambda_info = {
                "log_group": getattr(aws_context, "log_group_name", None),
                "log_stream": getattr(aws_context, "log_stream_name", None),
                "request_id": getattr(aws_context, "aws_request_id", None),
            }

    return lambda_info
