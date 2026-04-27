from functools import cache

from constants.general import IS_PRD
from services.aws.clients import ssm_client
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Prefix used in CFN template `{{resolve:ssm:/gitauto/X}}`. Every value resolved from this prefix is a GitAuto secret deployed via SSM Parameter Store and must be hidden from customer subprocess children. Operational env vars set inline in CFN (GIT_CONFIG_GLOBAL=/tmp/.gitconfig, S3_DEPENDENCY_BUCKET=...) are NOT in this prefix and pass through to subprocess.
SSM_GITAUTO_PREFIX = "/gitauto/"


@cache
@handle_exceptions(default_return_value=set(), raise_on_error=False)
def get_internal_env_var_names():
    """Names of GitAuto-internal env vars that must be scrubbed from subprocess children. Source of truth: SSM `/gitauto/*` parameter names — that's where every GitAuto secret lives in production. Cached for the lifetime of the process so cold start pays one DescribeParameters call.

    Sentry AGENT-3KJ/3KK/3KM/3KH/3KF/3KG: customer Node apps with @sentry/node loaded inherit SENTRY_DSN, init the SDK against our project, and pipe their app errors into our Sentry. The same exposure exists for OPENAI_API_KEY, GH_PRIVATE_KEY, STRIPE_API_KEY, SUPABASE_SERVICE_ROLE_KEY etc. — anything in /gitauto/.

    Locally (not IS_PRD) the scrub set is empty: no customer subprocess on a dev machine, no AWS IAM, no boto3 cold-start cost.
    """
    if not IS_PRD:
        logger.info("get_internal_env_var_names: non-prod, returning empty set")
        return set()

    logger.info("get_internal_env_var_names: querying SSM %s*", SSM_GITAUTO_PREFIX)
    paginator = ssm_client.get_paginator("describe_parameters")
    names: set[str] = set()
    for page in paginator.paginate(
        ParameterFilters=[
            {
                "Key": "Name",
                "Option": "BeginsWith",
                "Values": [SSM_GITAUTO_PREFIX],
            }
        ]
    ):
        for param in page["Parameters"]:
            full_name = param.get("Name")
            if not full_name:
                logger.warning(
                    "get_internal_env_var_names: SSM page param missing Name"
                )
                continue
            names.add(full_name.removeprefix(SSM_GITAUTO_PREFIX))

    logger.info("get_internal_env_var_names: %d names", len(names))
    return names
