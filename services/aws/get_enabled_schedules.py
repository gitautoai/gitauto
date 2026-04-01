from services.aws.clients import scheduler_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=set(), raise_on_error=False)
def get_enabled_schedules():
    """Return set of (owner_id, repo_id) for all enabled EventBridge schedules."""
    repo_keys: set[tuple[int, int]] = set()
    next_token = None

    while True:
        if next_token:
            response = scheduler_client.list_schedules(NextToken=next_token)
        else:
            response = scheduler_client.list_schedules()

        for schedule in response.get("Schedules", []):
            state = schedule.get("State", "")
            name = schedule.get("Name", "")
            if state == "ENABLED" and name.startswith("gitauto-repo-"):
                parts = name.replace("gitauto-repo-", "").split("-")
                repo_keys.add((int(parts[0]), int(parts[1])))

        next_token = response.get("NextToken")
        if not next_token:
            break

    return repo_keys
