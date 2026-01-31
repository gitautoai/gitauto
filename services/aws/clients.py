# Third-party imports
import boto3
from mypy_boto3_codebuild import CodeBuildClient
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_logs import CloudWatchLogsClient
from mypy_boto3_scheduler import EventBridgeSchedulerClient

from constants.aws import AWS_REGION

codebuild_client: CodeBuildClient = boto3.client("codebuild", region_name=AWS_REGION)

ec2_client: EC2Client = boto3.client("ec2", region_name=AWS_REGION)

lambda_client: LambdaClient = boto3.client("lambda", region_name=AWS_REGION)

logs_client: CloudWatchLogsClient = boto3.client("logs", region_name=AWS_REGION)

scheduler_client: EventBridgeSchedulerClient = boto3.client(
    "scheduler", region_name=AWS_REGION
)
