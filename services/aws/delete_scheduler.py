# Third party imports
from botocore.exceptions import ClientError

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from services.aws.clients import scheduler_client


@handle_exceptions(default_return_value=False, raise_on_error=False)
def delete_scheduler(schedule_name: str):
    try:
        scheduler_client.delete_schedule(Name=schedule_name)
        logger.info("Deleted EventBridge Scheduler: %s", schedule_name)
        return True

    except ClientError as err:
        if err.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
            logger.info("EventBridge Scheduler already deleted: %s", schedule_name)
            return True
        raise
