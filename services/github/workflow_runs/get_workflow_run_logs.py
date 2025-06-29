# Standard libraries
import io
import zipfile

# Third-party libraries
from requests import get

# Internal libraries
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.github.utils.create_headers import create_headers
from services.github.workflow_runs.get_failed_step_log_file_name import (
    get_failed_step_log_file_name,
)
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_workflow_run_logs(owner: str, repo: str, run_id: int, token: str):
    """https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#download-workflow-run-logs"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
    headers = create_headers(media_type="", token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    if response.status_code == 404 and "Not Found" in response.text:
        return response.status_code
    response.raise_for_status()

    # Get the failed step file name (ex: build/6_Run pytest.txt)
    failed_step_fname = get_failed_step_log_file_name(
        owner=owner, repo=repo, run_id=run_id, token=token
    )
    if failed_step_fname == 404:
        return failed_step_fname

    # Read the content of the zip file
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        for log_fname in zf.namelist():
            # ex: 0_build.txt
            # ex: build/system.txt
            # ex: build/1_Set up job.txt
            # ex: build/2_Run actions_checkout@v4.txt
            # ex: build/3_Set up Python 3.12.txt
            # ex: build/4_Install pytest.txt
            # ex: build/5_Set PYTHONPATH.txt
            # ex: build/6_Run pytest.txt
            if log_fname != failed_step_fname:
                continue

            # Remove the first 28 characters from the log content
            # E.g. "2024-10-18T23:27:40.6602932Z "
            with zf.open(name=log_fname) as lf:
                content = lf.read().decode(encoding=UTF8)
                content = "\n".join(
                    line[29:] if len(line) > 29 else line
                    for line in content.splitlines()
                )
                content = f"```GitHub Check Run Log: {log_fname}\n{content}\n```"
                return content

    return None
