from fastapi import Request
from payloads.aws.lambda_types import LambdaContext
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value={}, raise_on_error=False)
def extract_lambda_info(request: Request):
    logger.debug("Request scope: %s", request.scope)
    lambda_info: dict[str, str | None] = {}

    # https://mangum.fastapiexpert.com/adapter/
    if "aws.context" in request.scope:
        aws_context: LambdaContext = request.scope["aws.context"]
        logger.info("Lambda context: %s", aws_context)
        lambda_info = {
            "log_group": getattr(aws_context, "log_group_name", None),
            "log_stream": getattr(aws_context, "log_stream_name", None),
            "request_id": getattr(aws_context, "aws_request_id", None),
        }

    return lambda_info
