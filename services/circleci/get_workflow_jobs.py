# Third-party libraries
from requests import get

# Internal libraries
from config import TIMEOUT
from services.circleci.types import CircleCIWorkflowJob, CircleCIWorkflowJobsData
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_circleci_workflow_jobs(workflow_id: str, circle_token: str):
    """https://circleci.com/docs/api/v2/#operation/listWorkflowJobs"""
    base_url = "https://circleci.com/api/v2"
    url = f"{base_url}/workflow/{workflow_id}/job"
    headers = {"Circle-Token": circle_token}

    response = get(url=url, headers=headers, timeout=TIMEOUT)
    if response.status_code == 404:
        return list[CircleCIWorkflowJob]()
    response.raise_for_status()

    data: CircleCIWorkflowJobsData = response.json()
    return data.get("items", [])
