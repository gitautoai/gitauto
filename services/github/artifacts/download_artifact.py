# Standard libraries
import io
import zipfile

# Third-party libraries
from requests import get

# Internal libraries
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def download_artifact(owner: str, repo: str, artifact_id: int, token: str):
    """https://docs.github.com/en/rest/actions/artifacts?apiVersion=2022-11-28#download-an-artifact"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
    headers = create_headers(token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    zip_content = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_content) as zip_file:
        file_list = zip_file.namelist()
        print(f"File list: {file_list}")
        if "lcov.info" not in file_list:
            return None
        with zip_file.open("lcov.info") as lcov_file:
            return lcov_file.read().decode(UTF8)
