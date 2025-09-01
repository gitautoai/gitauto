# Third-party libraries
from requests import get

# Internal libraries
from config import TIMEOUT
from services.circleci.circleci_types import CircleCIArtifact, CircleCIJobArtifactsData
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_circleci_job_artifacts(project_slug: str, job_number: str, circle_token: str):
    # https://circleci.com/docs/api/v2/#operation/getJobArtifacts
    base_url = "https://circleci.com/api/v2"
    url = f"{base_url}/project/{project_slug}/{job_number}/artifacts"
    headers = {"Circle-Token": circle_token}

    response = get(url=url, headers=headers, timeout=TIMEOUT)
    if response.status_code == 404:
        return list[CircleCIArtifact]()
    response.raise_for_status()

    data: CircleCIJobArtifactsData = response.json()
    return data.get("items", [])
