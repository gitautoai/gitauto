import requests
from config import TIMEOUT, UTF8
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def download_circleci_artifact(artifact_url: str, token: str):
    # https://circleci.com/docs/api/v2/index.html#operation/getJobArtifacts
    headers = {"Circle-Token": token}
    response = requests.get(artifact_url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    content: str = response.content.decode(UTF8)
    return content
