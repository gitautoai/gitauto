import boto3
from mypy_boto3_ssm import SSMClient

from constants.aws import NAT_INSTANCE_ID
from constants.general import IS_PRD
from services.supabase.npm_tokens.get_npm_token import get_npm_token
from utils.logging.logging_config import logger


def run_install_via_ssm(
    efs_dir: str,
    owner_id: int,
    pkg_manager: str = "yarn",
):
    if not IS_PRD:
        logger.info("ssm: Skipping in non-prod environment")
        return None

    if not NAT_INSTANCE_ID:
        logger.error("ssm: NAT_INSTANCE_ID not configured")
        return None

    npm_token = get_npm_token(owner_id)
    if npm_token:
        env_prefix = f"export NPM_TOKEN={npm_token} && "
    else:
        env_prefix = ""

    command = f"{env_prefix}cd {efs_dir} && {pkg_manager} install"

    ssm: SSMClient = boto3.client("ssm", region_name="us-west-1")
    response = ssm.send_command(
        InstanceIds=[NAT_INSTANCE_ID],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [command]},
        TimeoutSeconds=1800,
        Comment=f"Install packages in {efs_dir}",
    )

    command_id = response["Command"].get("CommandId")
    logger.info("ssm: Sent install command %s for %s", command_id, efs_dir)
    return command_id
