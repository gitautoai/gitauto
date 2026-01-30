from constants.general import IS_PRD
from services.aws.clients import ssm_client
from services.aws.get_nat_instance_id import get_nat_instance_id
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

    nat_instance_id = get_nat_instance_id()
    if not nat_instance_id:
        logger.error("ssm: NAT instance not found")
        return None

    npm_token = get_npm_token(owner_id)
    if npm_token:
        env_prefix = f"export NPM_TOKEN={npm_token} && "
    else:
        env_prefix = ""

    command = f"{env_prefix}cd {efs_dir} && {pkg_manager} install"

    response = ssm_client.send_command(
        InstanceIds=[nat_instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [command]},
        TimeoutSeconds=1800,
        Comment=f"Install packages in {efs_dir}",
    )

    command_id = response["Command"].get("CommandId")
    logger.info("ssm: Sent install command %s for %s", command_id, efs_dir)
    return command_id
