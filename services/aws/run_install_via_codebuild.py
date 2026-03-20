import os
import shutil

from mypy_boto3_codebuild.type_defs import EnvironmentVariableTypeDef

from constants.general import IS_PRD
from services.aws.clients import codebuild_client
from services.node.detect_package_manager import PACKAGE_MANAGER_TO_LOCK_FILE
from services.supabase.npm_tokens.get_npm_token import get_npm_token
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Path to the JS script inside the Lambda container (copied from our repo via Dockerfile)
_MONGOD_SCRIPT_SRC = os.path.join(
    os.path.dirname(__file__), "download_mongod_binary.mjs"
)

# Shared location on EFS where CodeBuild can find the script
_MONGOD_SCRIPT_EFS = "/mnt/efs/.scripts/download_mongod_binary.mjs"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def run_install_via_codebuild(
    efs_dir: str,
    owner_id: int,
    pkg_manager: str,
):
    if not IS_PRD:
        logger.info("codebuild: Skipping in non-prod environment")
        return None

    # Copy the mongod download script to EFS so CodeBuild can run it
    if pkg_manager in PACKAGE_MANAGER_TO_LOCK_FILE and os.path.isfile(
        _MONGOD_SCRIPT_SRC
    ):
        os.makedirs(os.path.dirname(_MONGOD_SCRIPT_EFS), exist_ok=True)
        shutil.copy2(_MONGOD_SCRIPT_SRC, _MONGOD_SCRIPT_EFS)
        logger.info(
            "codebuild: Copied mongod download script to %s", _MONGOD_SCRIPT_EFS
        )

    env_overrides: list[EnvironmentVariableTypeDef] = [
        {"name": "EFS_DIR", "value": efs_dir, "type": "PLAINTEXT"},
        {"name": "PKG_MANAGER", "value": pkg_manager, "type": "PLAINTEXT"},
    ]

    npm_token = get_npm_token(owner_id)
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
    logger.info("codebuild: Started build %s for %s", build_id, efs_dir)
    return build_id
