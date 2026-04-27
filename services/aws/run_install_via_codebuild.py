from mypy_boto3_codebuild.type_defs import EnvironmentVariableTypeDef

from constants.aws import S3_DEPENDENCY_BUCKET
from constants.general import IS_PRD
from constants.node import FALLBACK_NODE_VERSION
from services.aws.clients import codebuild_client
from services.supabase.npm_tokens.get_npm_token import get_npm_token
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def run_install_via_codebuild(
    s3_key_prefix: str,  # e.g. "Foxquilt/foxcom-forms" — S3 path for manifests and tarballs
    owner_id: int,
    pkg_manager: str,
    node_version: str = FALLBACK_NODE_VERSION,
):
    if not IS_PRD:
        logger.info("codebuild: Skipping in non-prod environment")
        return None

    env_overrides: list[EnvironmentVariableTypeDef] = [
        {"name": "S3_BUCKET", "value": S3_DEPENDENCY_BUCKET, "type": "PLAINTEXT"},
        {"name": "S3_KEY_PREFIX", "value": s3_key_prefix, "type": "PLAINTEXT"},
        {"name": "PKG_MANAGER", "value": pkg_manager, "type": "PLAINTEXT"},
        {"name": "NODE_VERSION", "value": node_version, "type": "PLAINTEXT"},
    ]

    npm_token = get_npm_token(platform="github", owner_id=owner_id)
    if npm_token:
        env_overrides.append(
            {"name": "NPM_TOKEN", "value": npm_token, "type": "PLAINTEXT"}
        )
        logger.info("codebuild: NPM_TOKEN added for owner_id %s", owner_id)

    # https://docs.aws.amazon.com/codebuild/latest/APIReference/API_StartBuild.html
    response = codebuild_client.start_build(
        projectName="gitauto-package-install",
        environmentVariablesOverride=env_overrides,
    )

    build_id = response["build"].get("id")
    logger.info("codebuild: Started build %s for %s", build_id, s3_key_prefix)
    return build_id
