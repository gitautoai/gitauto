# Third-party imports
import boto3
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_logs import CloudWatchLogsClient
from mypy_boto3_scheduler import EventBridgeSchedulerClient

AWS_REGION = "us-west-1"

lambda_client: LambdaClient = boto3.client("lambda", region_name=AWS_REGION)

logs_client: CloudWatchLogsClient = boto3.client("logs", region_name=AWS_REGION)

scheduler_client: EventBridgeSchedulerClient = boto3.client(
    "scheduler", region_name=AWS_REGION
)
