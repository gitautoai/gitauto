# Third-party libraries
import requests

# Internal libraries
from config import TIMEOUT
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_pipeline_workflows(pipeline_id: str, circle_token: str):
    # https://circleci.com/docs/api/v2/index.html#tag/Workflow/operation/listWorkflowsByPipelineId
    base_url = "https://circleci.com/api/v2"
    url = f"{base_url}/pipeline/{pipeline_id}/workflow"
    headers = {"Circle-Token": circle_token}

    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    if response.status_code == 404:
        return []
    response.raise_for_status()

    data = response.json()
    return data.get("items", [])
