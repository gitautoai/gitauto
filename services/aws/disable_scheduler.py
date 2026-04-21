# pyright: reportAssignmentType=false
# Third party imports
from botocore.exceptions import ClientError
from mypy_boto3_scheduler.type_defs import UpdateScheduleInputTypeDef

# Local imports
from services.aws.clients import scheduler_client
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Derived from the SDK, not hardcoded — stays in sync with update_schedule's signature.
ALLOWED_UPDATE_FIELDS = frozenset(UpdateScheduleInputTypeDef.__annotations__)


@handle_exceptions(default_return_value=False, raise_on_error=False)
def disable_scheduler(schedule_name: str):
    try:
        current = scheduler_client.get_schedule(Name=schedule_name)
    except ClientError as err:
        if err.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
            logger.info("EventBridge Scheduler not found: %s", schedule_name)
            return True
        logger.error("EventBridge Scheduler get_schedule failed: %s", err)
        raise

    update_input: UpdateScheduleInputTypeDef = {
        k: v for k, v in current.items() if k in ALLOWED_UPDATE_FIELDS
    }
    update_input["State"] = "DISABLED"
    scheduler_client.update_schedule(**update_input)
    logger.info("Disabled EventBridge Scheduler: %s", schedule_name)
    return True
