# Standard imports
import logging

# Local imports
from services.aws.clients import scheduler_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def delete_scheduler(schedule_name: str):
    scheduler_client.delete_schedule(Name=schedule_name)
    logging.info("Deleted EventBridge Scheduler: %s", schedule_name)

    return True
