# pylint: disable=too-few-public-methods
from typing import Protocol


class LambdaContext(Protocol):
    """AWS Lambda runtime context object interface"""

    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: str
