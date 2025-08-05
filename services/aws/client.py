# Third-party imports
import boto3
from mypy_boto3_scheduler import EventBridgeSchedulerClient

# When running on AWS Lambda, credentials and region are automatically provided by IAM role
scheduler_client: EventBridgeSchedulerClient = boto3.client("scheduler")
