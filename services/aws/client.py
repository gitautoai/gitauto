# Third-party imports
import boto3
from mypy_boto3_scheduler import EventBridgeSchedulerClient

AWS_REGION = "us-west-1"

scheduler_client: EventBridgeSchedulerClient = boto3.client("scheduler", region_name=AWS_REGION)
