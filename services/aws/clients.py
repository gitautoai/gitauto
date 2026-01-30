# Third-party imports
import boto3
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_logs import CloudWatchLogsClient
from mypy_boto3_scheduler import EventBridgeSchedulerClient
from mypy_boto3_ssm import SSMClient

from constants.aws import AWS_REGION

ec2_client: EC2Client = boto3.client("ec2", region_name=AWS_REGION)

lambda_client: LambdaClient = boto3.client("lambda", region_name=AWS_REGION)

logs_client: CloudWatchLogsClient = boto3.client("logs", region_name=AWS_REGION)

scheduler_client: EventBridgeSchedulerClient = boto3.client(
    "scheduler", region_name=AWS_REGION
)

ssm_client: SSMClient = boto3.client("ssm", region_name=AWS_REGION)
