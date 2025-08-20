# Local imports
from services.aws.clients import scheduler_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_schedulers_by_owner_id(owner_id: int):
    schedules = []
    next_token = None

    while True:
        if next_token:
            response = scheduler_client.list_schedules(NextToken=next_token)
        else:
            response = scheduler_client.list_schedules()

        for schedule in response.get("Schedules", []):
            schedule_name = schedule.get("Name", "")
            # Match pattern: gitauto-repo-{ownerId}-{repoId} or gitauto-repo-{ownerId}-{repoId}-{index}
            if schedule_name.startswith(f"gitauto-repo-{owner_id}-"):
                schedules.append(schedule_name)

        next_token = response.get("NextToken")
        if not next_token:
            break

    return schedules
